from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_ARTIFACTS_PATH = (Path.home() / ".cache" / "docling" / "models").resolve()
UNKNOWN = "未明确"
LOW_TEXT_DENSITY_THRESHOLD = 80
LEGACY_ARTIFACTS = ("run_manifest.json", "main_text.md", "figure_index.md")


@dataclass(frozen=True)
class ParseArtifacts:
    parsed_md: Path
    parsed_json: Path
    figure_index_json: Path
    parse_status: Path


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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
        return UNKNOWN
    ref = caption_ref.get("$ref")
    if not isinstance(ref, str):
        return UNKNOWN
    text_obj = text_lookup.get(ref)
    if not text_obj:
        return UNKNOWN
    text = text_obj.get("text") or text_obj.get("orig") or UNKNOWN
    return str(text).strip() or UNKNOWN


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
) -> list[dict[str, object]]:
    import pypdfium2 as pdfium

    pictures = document_dict.get("pictures", [])
    if not isinstance(pictures, list):
        return []

    text_lookup = _text_lookup(document_dict)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(str(pdf_path))
    page_cache: dict[int, tuple[Any, float, float]] = {}
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
            caption_text = UNKNOWN
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

    return entries


def pdf_page_count(pdf_path: Path) -> int:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        return len(pdf)
    finally:
        pdf.close()


def _list_count(document_dict: dict[str, object], key: str) -> int:
    value = document_dict.get(key, [])
    return len(value) if isinstance(value, list) else 0


def _label_count(document_dict: dict[str, object], label: str) -> int:
    count = 0
    for key in ("texts", "tables", "pictures"):
        items = document_dict.get(key, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and str(item.get("label", "")).lower() == label:
                count += 1
    return count


def _visible_text(value: object) -> list[str]:
    fragments: list[str] = []
    if isinstance(value, dict):
        text = value.get("text")
        original = value.get("orig")
        if isinstance(text, str) and text.strip():
            fragments.append(text)
        elif isinstance(original, str) and original.strip():
            fragments.append(original)
        for key in ("data", "table_cells", "cells"):
            if key in value:
                fragments.extend(_visible_text(value[key]))
    elif isinstance(value, list):
        for item in value:
            fragments.extend(_visible_text(item))
    return fragments


def document_text_chars(document_dict: dict[str, object]) -> int:
    fragments: list[str] = []
    for key in ("texts", "tables"):
        fragments.extend(_visible_text(document_dict.get(key, [])))
    return len(re.sub(r"\s+", "", "".join(fragments)))


def build_parse_health(
    *,
    document_dict: dict[str, object],
    pages: int,
    exported_figures: int,
    ocr: bool,
) -> dict[str, object]:
    text_chars = document_text_chars(document_dict)
    chars_per_page = round(text_chars / pages, 2) if pages else 0.0
    pictures_detected = _list_count(document_dict, "pictures")
    warnings: list[str] = []
    if pages >= 2 and chars_per_page < LOW_TEXT_DENSITY_THRESHOLD:
        warnings.append("low_text_density")
        if not ocr:
            warnings.append("ocr_recommended")
    if pictures_detected > exported_figures:
        warnings.append("figure_export_incomplete")
    return {
        "pdf_pages": pages,
        "text_chars": text_chars,
        "text_chars_per_page": chars_per_page,
        "pictures_detected": pictures_detected,
        "figures_exported": exported_figures,
        "tables_detected": _list_count(document_dict, "tables"),
        "formulas_detected": _label_count(document_dict, "formula"),
        "code_items_detected": _label_count(document_dict, "code"),
        "warnings": warnings,
    }


def create_converter(
    *,
    ocr: bool = False,
    device: str = "auto",
    artifacts_path: Path | None = DEFAULT_ARTIFACTS_PATH,
) -> tuple[Any, str | None]:
    from docling.backend.docling_parse_backend import DoclingParseDocumentBackend
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

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
    converter: Any | None = None,
    resolved_artifacts_path: str | None = None,
) -> ParseArtifacts:
    pdf_path = pdf_path.expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    for legacy_name in LEGACY_ARTIFACTS:
        (output_dir / legacy_name).unlink(missing_ok=True)
    parse_status_path = output_dir / "status.json"
    artifacts = ParseArtifacts(
        parsed_md=output_dir / "parsed.md",
        parsed_json=output_dir / "parsed.json",
        figure_index_json=output_dir / "figure_index.json",
        parse_status=parse_status_path,
    )
    health: dict[str, object] | None = None
    try:
        if converter is None:
            converter, resolved_artifacts_path = create_converter(
                ocr=ocr,
                device=device,
                artifacts_path=artifacts_path,
            )
        result = converter.convert(str(pdf_path))
        document = result.document
        markdown = document.export_to_markdown()
        document_dict = document.export_to_dict()
        figure_entries = export_figures(pdf_path, document_dict, output_dir)
        health = build_parse_health(
            document_dict=document_dict,
            pages=pdf_page_count(pdf_path),
            exported_figures=len(figure_entries),
            ocr=ocr,
        )
        artifacts.parsed_md.write_text(markdown, encoding="utf-8")
        write_json(artifacts.parsed_json, document_dict)
        write_json(artifacts.figure_index_json, figure_entries)
        if health["pdf_pages"] == 0 or health["text_chars"] == 0:
            raise ValueError("Docling produced no usable page or text content.")
    except Exception as exc:
        message = (
            str(exc)
            if str(exc).startswith("Docling produced no usable")
            else (
                "Docling failed to parse or export the PDF. "
                "Verify that model artifacts are initialized and rerun with --ocr only if needed. "
                f"Original error: {exc}"
            )
        )
        parse_status = {
            "ok": False,
            "pdf_path": str(pdf_path.resolve()),
            "ocr_enabled": ocr,
            "device": device,
            "code_enrichment_enabled": True,
            "formula_enrichment_enabled": True,
            "selected_backend": "docling_parse",
            "artifacts_path": resolved_artifacts_path,
            "health": health,
            "error": message,
            "error_type": type(exc).__name__,
        }
        write_json(parse_status_path, parse_status)
        raise RuntimeError(message) from exc

    parse_status = {
        "ok": True,
        "pdf_path": str(pdf_path.resolve()),
        "ocr_enabled": ocr,
        "device": device,
        "code_enrichment_enabled": True,
        "formula_enrichment_enabled": True,
        "selected_backend": "docling_parse",
        "artifacts_path": resolved_artifacts_path,
        "health": health,
        "error": None,
        "error_type": None,
    }
    write_json(artifacts.parse_status, parse_status)
    return artifacts
