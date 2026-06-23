from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import pypdfium2 as pdfium
from docling.backend.docling_parse_backend import DoclingParseDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from PIL import Image

REQUIRED_ARTIFACTS = [
    "run_manifest.json",
    "status.json",
    "main_text.md",
    "parsed.md",
    "parsed.json",
    "figure_index.json",
    "figure_index.md",
    "figures",
]
DEFAULT_ARTIFACTS_PATH = (Path.home() / ".cache" / "docling" / "models").resolve()
MAIN_TEXT_BOUNDARY_HEADINGS = {
    "references",
    "bibliography",
    "acknowledgements",
    "acknowledgments",
}
MAIN_TEXT_BOUNDARY_PREFIXES = (
    "appendix",
    "appendices",
    "supplementary",
)


@dataclass(frozen=True)
class ParseArtifacts:
    main_text: Path
    parsed_md: Path
    parsed_json: Path
    figure_index_json: Path
    figure_index_md: Path
    parse_status: Path
    manifest: Path


def is_main_text_boundary(line: str) -> bool:
    match = re.match(r"^#{1,6}\s+(.+?)\s*$", line.strip())
    if not match:
        return False
    heading = re.sub(r"\s+", " ", match.group(1).strip()).lower().strip(":")
    heading = re.sub(r"^\d+(?:\.\d+)*\s+", "", heading)
    return heading in MAIN_TEXT_BOUNDARY_HEADINGS or heading.startswith(MAIN_TEXT_BOUNDARY_PREFIXES)


def extract_main_text(markdown: str) -> str:
    offset = 0
    for line in markdown.splitlines(keepends=True):
        if is_main_text_boundary(line):
            return markdown[:offset].rstrip() + "\n"
        offset += len(line)
    return markdown


def _text_lookup(document_dict: dict[str, object]) -> dict[str, dict[str, object]]:
    texts = document_dict.get("texts", [])
    if not isinstance(texts, list):
        return {}
    lookup: dict[str, dict[str, object]] = {}
    for item in texts:
        if isinstance(item, dict) and "self_ref" in item:
            lookup[str(item["self_ref"])] = item
    return lookup


def _safe_caption_text(caption_ref: object, text_lookup: dict[str, dict[str, object]]) -> str:
    if not isinstance(caption_ref, dict):
        return "not_specified"
    ref = caption_ref.get("$ref")
    if not isinstance(ref, str):
        return "not_specified"
    text_obj = text_lookup.get(ref)
    if not text_obj:
        return "not_specified"
    text = text_obj.get("text") or text_obj.get("orig") or "not_specified"
    return str(text).strip() or "not_specified"


def _pdf_bbox_to_pil_crop(
    bbox: dict[str, object], page_width: float, page_height: float, scale: float
) -> tuple[int, int, int, int]:
    left = float(bbox["l"])
    right = float(bbox["r"])
    top = float(bbox["t"])
    bottom = float(bbox["b"])
    x0 = max(0.0, min(left, right))
    x1 = min(page_width, max(left, right))
    y0 = max(0.0, page_height - max(top, bottom))
    y1 = min(page_height, page_height - min(top, bottom))
    return (
        int(x0 * scale),
        int(y0 * scale),
        int(x1 * scale),
        int(y1 * scale),
    )


def export_figures(
    pdf_path: Path,
    document_dict: dict[str, object],
    output_dir: Path,
    scale: float = 2.0,
) -> tuple[list[dict[str, object]], str]:
    pictures = document_dict.get("pictures", [])
    if not isinstance(pictures, list):
        return [], "# Figures\n\nNo figures extracted.\n"

    text_lookup = _text_lookup(document_dict)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(str(pdf_path))
    page_cache: dict[int, tuple[Image.Image, float, float]] = {}
    entries: list[dict[str, object]] = []

    try:
        for pic_idx, picture in enumerate(pictures, 1):
            if not isinstance(picture, dict):
                continue
            prov_list = picture.get("prov")
            if not isinstance(prov_list, list) or not prov_list:
                continue
            prov = prov_list[0]
            if not isinstance(prov, dict):
                continue
            page_no = prov.get("page_no")
            bbox = prov.get("bbox")
            if not isinstance(page_no, int) or not isinstance(bbox, dict):
                continue
            page_index = page_no - 1
            if page_index < 0 or page_index >= len(pdf):
                continue
            if page_index not in page_cache:
                page = pdf[page_index]
                page_width, page_height = page.get_size()
                bitmap = page.render(scale=scale)
                page_cache[page_index] = (bitmap.to_pil(), page_width, page_height)
            pil_image, page_width, page_height = page_cache[page_index]
            crop_box = _pdf_bbox_to_pil_crop(bbox, page_width, page_height, scale)
            if crop_box[2] <= crop_box[0] or crop_box[3] <= crop_box[1]:
                continue
            cropped = pil_image.crop(crop_box)
            image_name = f"figure-{pic_idx:02d}.png"
            image_path = figures_dir / image_name
            relative_image_path = image_path.relative_to(output_dir).as_posix()
            cropped.save(image_path)
            captions = picture.get("captions", [])
            caption_text = "not_specified"
            if isinstance(captions, list) and captions:
                caption_text = _safe_caption_text(captions[0], text_lookup)
            entries.append(
                {
                    "figure_id": f"figure-{pic_idx:02d}",
                    "page_no": page_no,
                    "image_path": relative_image_path,
                    "caption": caption_text,
                }
            )
    finally:
        pdf.close()

    lines = ["# Figures", ""]
    if not entries:
        lines.append("No figures extracted.")
    else:
        for entry in entries:
            rel_path = str(entry["image_path"])
            lines.extend(
                [
                    f"## {entry['figure_id']}",
                    f"- Page: {entry['page_no']}",
                    f"- Image Path: {entry['image_path']}",
                    f"- Caption: {entry['caption']}",
                    "",
                    f"![{entry['figure_id']}]({rel_path})",
                    "",
                ]
            )
    return entries, "\n".join(lines).strip() + "\n"


def build_manifest(output_dir: Path, pdf_path: Path) -> dict[str, object]:
    return {
        "pdf_path": str(pdf_path.resolve()),
        "output_dir": str(output_dir.resolve()),
        "artifacts": {
            name: str((output_dir / name).resolve()) for name in REQUIRED_ARTIFACTS
        },
    }


def create_converter(
    *,
    ocr: bool = False,
    device: str = "auto",
    artifacts_path: Path | None = DEFAULT_ARTIFACTS_PATH,
) -> tuple[DocumentConverter, str | None]:
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = ocr
    pipeline_options.do_code_enrichment = True
    pipeline_options.do_formula_enrichment = True
    pipeline_options.accelerator_options.device = device
    resolved_artifacts_path = None
    if artifacts_path is not None:
        resolved_artifacts_path = str(artifacts_path.expanduser().resolve())
        pipeline_options.artifacts_path = resolved_artifacts_path
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                backend=DoclingParseDocumentBackend,
            ),
        }
    )
    return converter, resolved_artifacts_path


def parse_pdf(
    *,
    pdf_path: Path,
    output_dir: Path,
    ocr: bool = False,
    device: str = "auto",
    artifacts_path: Path | None = DEFAULT_ARTIFACTS_PATH,
    converter: DocumentConverter | None = None,
    resolved_artifacts_path: str | None = None,
) -> ParseArtifacts:
    pdf_path = pdf_path.expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "run_manifest.json"
    parse_status_path = output_dir / "status.json"
    manifest_path.write_text(
        json.dumps(build_manifest(output_dir, pdf_path), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if converter is None:
        converter, resolved_artifacts_path = create_converter(
            ocr=ocr,
            device=device,
            artifacts_path=artifacts_path,
        )

    try:
        result = converter.convert(str(pdf_path))
    except Exception as exc:
        parse_status = {
            "ok": False,
            "pdf_path": str(pdf_path.resolve()),
            "ocr_enabled": ocr,
            "device": device,
            "code_enrichment_enabled": True,
            "formula_enrichment_enabled": True,
            "selected_backend": "docling_parse",
            "artifacts_path": resolved_artifacts_path,
            "error": (
                "Docling failed to parse the PDF. "
                "Verify that model artifacts are initialized and rerun with --ocr only if needed. "
                f"Original error: {exc}"
            ),
            "error_type": type(exc).__name__,
        }
        parse_status_path.write_text(
            json.dumps(parse_status, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        raise RuntimeError(parse_status["error"]) from exc

    document = result.document
    markdown = document.export_to_markdown()
    document_dict = document.export_to_dict()
    figure_entries, figure_index_md = export_figures(pdf_path, document_dict, output_dir)

    artifacts = ParseArtifacts(
        main_text=output_dir / "main_text.md",
        parsed_md=output_dir / "parsed.md",
        parsed_json=output_dir / "parsed.json",
        figure_index_json=output_dir / "figure_index.json",
        figure_index_md=output_dir / "figure_index.md",
        parse_status=parse_status_path,
        manifest=manifest_path,
    )
    artifacts.main_text.write_text(extract_main_text(markdown), encoding="utf-8")
    artifacts.parsed_md.write_text(markdown, encoding="utf-8")
    artifacts.parsed_json.write_text(
        json.dumps(document_dict, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    artifacts.figure_index_json.write_text(
        json.dumps(figure_entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    artifacts.figure_index_md.write_text(figure_index_md, encoding="utf-8")
    parse_status = {
        "ok": True,
        "pdf_path": str(pdf_path.resolve()),
        "ocr_enabled": ocr,
        "device": device,
        "code_enrichment_enabled": True,
        "formula_enrichment_enabled": True,
        "selected_backend": "docling_parse",
        "artifacts_path": resolved_artifacts_path,
        "error": None,
        "error_type": None,
    }
    artifacts.parse_status.write_text(
        json.dumps(parse_status, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return artifacts
