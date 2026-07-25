#!/usr/bin/env python3
from __future__ import annotations

import argparse
import filecmp
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE_PATH = SKILL_DIR / "assets" / "summary_template.json"
UNKNOWN = "未明确"
MIN_EXCERPT_LENGTH = 12
MAX_EXCERPT_LENGTH = 300
WRAPPER_PATTERNS = (
    re.compile(r"(?:下面|以下)(?:将|先|再)?(?:整理|介绍|说明)"),
    re.compile(r"本节(?:将|主要|下面)"),
    re.compile(r"接下来(?:将|我们)"),
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value))
    return re.sub(r"\s+", " ", text).strip()


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def metadata_author_value(metadata: dict[str, object]) -> str:
    authors = metadata.get("authors", [])
    if authors is None:
        return UNKNOWN
    if not isinstance(authors, list):
        return UNKNOWN
    names: list[str] = []
    for author in authors:
        if isinstance(author, dict):
            name = normalize_text(author.get("name", ""))
        else:
            name = normalize_text(author)
        if name:
            names.append(name)
    return "、".join(names) if names else UNKNOWN


def metadata_text_value(metadata: dict[str, object], key: str) -> str:
    raw_value = metadata.get(key)
    if raw_value is None:
        return UNKNOWN
    value = normalize_text(raw_value)
    return value or UNKNOWN


def summary_title(text: str) -> str | None:
    for line in text.splitlines():
        match = re.fullmatch(r"#\s+(.+?)\s*", line)
        if match:
            return normalize_text(match.group(1))
    return None


def summary_header_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = re.fullmatch(r"-\s*([^：:]+)[：:]\s*(.*?)\s*", line)
        if match:
            fields[normalize_text(match.group(1))] = normalize_text(match.group(2))
    return fields


def item_pages(item: dict[str, object]) -> list[int]:
    prov = item.get("prov", [])
    if not isinstance(prov, list):
        return []
    pages: list[int] = []
    for entry in prov:
        if isinstance(entry, dict) and isinstance(entry.get("page_no"), int):
            pages.append(int(entry["page_no"]))
    return pages


def visible_strings(value: object) -> list[str]:
    strings: list[str] = []
    if isinstance(value, dict):
        text = value.get("text")
        original = value.get("orig")
        if isinstance(text, (str, int, float)) and normalize_text(text):
            strings.append(normalize_text(text))
        elif isinstance(original, (str, int, float)) and normalize_text(original):
            strings.append(normalize_text(original))
        for key in ("data", "table_cells", "cells"):
            if key in value:
                strings.extend(visible_strings(value[key]))
    elif isinstance(value, list):
        for child in value:
            strings.extend(visible_strings(child))
    return strings


def build_page_fragments(document: dict[str, object]) -> dict[int, list[str]]:
    page_fragments: dict[int, list[str]] = {}
    for collection_name in ("texts", "tables", "pictures"):
        collection = document.get(collection_name, [])
        if not isinstance(collection, list):
            continue
        for item in collection:
            if not isinstance(item, dict):
                continue
            strings = visible_strings(item)
            if not strings:
                continue
            pages = set(item_pages(item))
            if len(pages) == 1:
                page_fragments.setdefault(next(iter(pages)), []).extend(strings)
    return page_fragments


def required_evidence_keys(template: dict[str, object]) -> list[str]:
    keys: list[str] = []
    core = template.get("core_conclusion")
    if isinstance(core, dict) and isinstance(core.get("evidence_key"), str):
        keys.append(str(core["evidence_key"]))
    sections = template.get("sections", [])
    if isinstance(sections, list):
        for section in sections:
            if isinstance(section, dict) and isinstance(section.get("evidence_key"), str):
                keys.append(str(section["evidence_key"]))
    return keys


def validate_figure_index(
    entries: object,
    *,
    pdf_pages: int,
) -> tuple[dict[str, dict[str, object]], dict[str, str], list[str]]:
    by_id: dict[str, dict[str, object]] = {}
    image_paths: dict[str, str] = {}
    errors: list[str] = []
    if not isinstance(entries, list):
        return {}, {}, ["figure index must be a JSON array"]
    for index, entry in enumerate(entries, 1):
        prefix = f"figure_index[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        figure_id = entry.get("figure_id")
        page_no = entry.get("page_no")
        image_path = entry.get("image_path")
        if not isinstance(figure_id, str) or not figure_id:
            errors.append(f"{prefix} has invalid figure_id")
            continue
        if figure_id in by_id:
            errors.append(f"{prefix} duplicates figure_id {figure_id}")
            continue
        if (
            not isinstance(page_no, int)
            or isinstance(page_no, bool)
            or page_no < 1
            or page_no > pdf_pages
        ):
            errors.append(f"{prefix} has invalid page_no")
        if not isinstance(image_path, str) or not image_path:
            errors.append(f"{prefix} has invalid image_path")
            continue
        name = Path(image_path).name
        if name in image_paths:
            errors.append(f"{prefix} duplicates image basename {name}")
        by_id[figure_id] = entry
        image_paths[name] = image_path
    return by_id, image_paths, errors


def validate_evidence(
    evidence_document: object,
    *,
    template: dict[str, object],
    page_fragments: dict[int, list[str]],
    pdf_pages: int,
    figures: dict[str, dict[str, object]],
) -> list[str]:
    errors: list[str] = []
    if not isinstance(evidence_document, dict) or evidence_document.get("version") != 1:
        return ["summary_evidence.json must use version 1"]
    evidence = evidence_document.get("evidence")
    if not isinstance(evidence, dict):
        return ["summary_evidence.json must contain an evidence object"]

    for key in required_evidence_keys(template):
        entries = evidence.get(key)
        if not isinstance(entries, list) or not entries:
            errors.append(f"missing evidence for {key}")
            continue
        for index, entry in enumerate(entries, 1):
            prefix = f"{key}[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{prefix} must be an object")
                continue
            page = entry.get("page")
            raw_excerpt = entry.get("excerpt")
            if not isinstance(raw_excerpt, str):
                errors.append(f"{prefix} excerpt must be a string")
                continue
            excerpt = normalize_text(raw_excerpt)
            if not isinstance(page, int) or isinstance(page, bool) or page < 1 or page > pdf_pages:
                errors.append(f"{prefix} has invalid page")
                continue
            if not MIN_EXCERPT_LENGTH <= len(excerpt) <= MAX_EXCERPT_LENGTH:
                errors.append(
                    f"{prefix} excerpt length must be {MIN_EXCERPT_LENGTH}-{MAX_EXCERPT_LENGTH}"
                )
            elif not any(excerpt in fragment for fragment in page_fragments.get(page, [])):
                errors.append(f"{prefix} excerpt was not found on page {page}")
            figure_id = entry.get("figure_id")
            if figure_id is not None:
                figure = figures.get(str(figure_id))
                if figure is None:
                    errors.append(f"{prefix} references unknown figure_id {figure_id}")
                elif figure.get("page_no") != page:
                    errors.append(f"{prefix} figure_id page does not match evidence page")
    return errors


def markdown_image_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")]
    title_match = re.fullmatch(r"""(.+?)\s+(?:"[^"]*"|'[^']*')""", target)
    return title_match.group(1) if title_match else target


def markdown_image_targets(text: str) -> list[str]:
    targets: list[str] = []
    cursor = 0
    while True:
        image_start = text.find("![", cursor)
        if image_start < 0:
            break
        alt_end = text.find("]", image_start + 2)
        if alt_end < 0 or alt_end + 1 >= len(text) or text[alt_end + 1] != "(":
            cursor = image_start + 2
            continue
        target_start = alt_end
        index = target_start + 2
        depth = 1
        escaped = False
        while index < len(text):
            char = text[index]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    targets.append(markdown_image_target(text[target_start + 2 : index]))
                    cursor = index + 1
                    break
            index += 1
        else:
            break
    return targets


def validate_images(
    text: str,
    *,
    summary_path: Path,
    figures_dir: Path,
    parse_dir: Path,
    indexed_image_paths: dict[str, str],
) -> list[str]:
    errors: list[str] = []
    targets = markdown_image_targets(text)
    if len(targets) > 3:
        errors.append("summary references more than 3 images")
    for target in targets:
        if re.match(r"^[a-z][a-z0-9+.-]*://", target, flags=re.IGNORECASE):
            errors.append(f"summary image must be local: {target}")
            continue
        resolved = (summary_path.parent / target).resolve()
        if not path_is_within(resolved, figures_dir):
            errors.append(f"summary image is outside figures directory: {target}")
        elif not resolved.is_file():
            errors.append(f"summary image does not exist: {target}")
        elif resolved.name not in indexed_image_paths:
            errors.append(f"summary image is not present in figure index: {target}")
        else:
            source = (parse_dir / indexed_image_paths[resolved.name]).resolve()
            if not path_is_within(source, parse_dir) or not source.is_file():
                errors.append(f"indexed source image does not exist: {target}")
            elif not filecmp.cmp(resolved, source, shallow=False):
                errors.append(f"summary image differs from indexed source: {target}")
    return errors


def validate_metadata(
    text: str,
    metadata: dict[str, object],
) -> list[str]:
    errors: list[str] = []
    expected_title = metadata_text_value(metadata, "title")
    actual_title = summary_title(text)
    if actual_title != expected_title:
        errors.append(f"title does not match metadata: expected {expected_title}")

    fields = summary_header_fields(text)
    expected_fields = {
        "作者": metadata_author_value(metadata),
        "发布时间": metadata_text_value(metadata, "published_at"),
        "论文链接": metadata_text_value(metadata, "paper_link"),
    }
    for field, expected in expected_fields.items():
        if fields.get(field) != expected:
            errors.append(f"{field} does not match metadata: expected {expected}")
    if "代码链接" in fields:
        expected_code_link = metadata_text_value(metadata, "code_link")
        if fields["代码链接"] != expected_code_link:
            errors.append(f"代码链接 does not match metadata: expected {expected_code_link}")
    return errors


def wrapper_warnings(text: str) -> list[str]:
    return [
        f"wrapper_expression:{pattern.pattern}"
        for pattern in WRAPPER_PATTERNS
        if pattern.search(text)
    ]


def load_json_input(path: Path, label: str, errors: list[object]) -> object | None:
    if not path.is_file():
        return None
    try:
        return read_json(path)
    except (OSError, ValueError) as exc:
        errors.append(f"{label} is invalid JSON: {exc}")
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a paper summary and update its import status."
    )
    parser.add_argument("summary", type=Path, help="Path to the Raw summary Markdown")
    parser.add_argument("--work-dir", type=Path, required=True, help="Import workspace _work directory")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE_PATH, help="Template JSON path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary_path = args.summary.expanduser().resolve()
    work_dir = args.work_dir.expanduser().resolve()
    template_path = args.template.expanduser().resolve()
    validation_path = work_dir / "summarize" / "validation.json"
    evidence_path = work_dir / "summarize" / "summary_evidence.json"
    parse_status_path = work_dir / "parse" / "status.json"
    parsed_json_path = work_dir / "parse" / "parsed.json"
    figure_index_path = work_dir / "parse" / "figure_index.json"
    status_path = work_dir / "status.json"
    metadata_path = work_dir.parent / "metadata.json"

    result: dict[str, object] = {
        "summary_path": str(summary_path),
        "template_path": str(template_path),
        "evidence_path": str(evidence_path),
        "valid": False,
        "errors": [],
        "warnings": [],
    }
    errors = result["errors"]
    warnings = result["warnings"]
    if not isinstance(errors, list) or not isinstance(warnings, list):
        raise TypeError("validation result lists are invalid")

    required_paths = {
        "summary": summary_path,
        "template": template_path,
        "aggregate status": status_path,
        "metadata": metadata_path,
        "parse status": parse_status_path,
        "parsed JSON": parsed_json_path,
        "figure index": figure_index_path,
        "summary evidence": evidence_path,
    }
    for label, path in required_paths.items():
        if not path.is_file():
            errors.append(f"{label} not found: {path}")

    aggregate_status: dict[str, object] = {}
    loaded_status = load_json_input(status_path, "aggregate status", errors)
    if isinstance(loaded_status, dict):
        aggregate_status = loaded_status
        expected_summary = aggregate_status.get("summary_path")
        if isinstance(expected_summary, str) and Path(expected_summary).expanduser().resolve() != summary_path:
            errors.append("summary path does not match aggregate status")
    elif loaded_status is not None:
        errors.append("aggregate status must be a JSON object")

    parse_ok = False
    pdf_pages = 0
    parse_status = load_json_input(parse_status_path, "parse status", errors)
    if isinstance(parse_status, dict):
        parse_ok = parse_status.get("ok") is True
        if not parse_ok:
            errors.append("parse status is not usable")
        health = parse_status.get("health")
        if not isinstance(health, dict):
            errors.append("parse health is missing")
        else:
            pdf_pages_value = health.get("pdf_pages")
            if isinstance(pdf_pages_value, int) and not isinstance(pdf_pages_value, bool):
                pdf_pages = pdf_pages_value
            else:
                errors.append("parse health has invalid pdf_pages")
            parse_warnings = health.get("warnings", [])
            if isinstance(parse_warnings, list):
                warnings.extend(str(item) for item in parse_warnings)
            else:
                errors.append("parse health warnings must be a list")
    elif parse_status is not None:
        errors.append("parse status must be a JSON object")

    template = load_json_input(template_path, "template", errors)
    metadata = load_json_input(metadata_path, "metadata", errors)
    document = load_json_input(parsed_json_path, "parsed JSON", errors)
    figure_entries = load_json_input(figure_index_path, "figure index", errors)
    evidence_document = load_json_input(evidence_path, "summary evidence", errors)

    if template is not None and not isinstance(template, dict):
        errors.append("template must be a JSON object")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append("metadata must be a JSON object")
    if document is not None and not isinstance(document, dict):
        errors.append("parsed JSON must be an object")

    text: str | None = None
    if summary_path.is_file():
        try:
            text = summary_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"summary cannot be read as UTF-8: {exc}")
        else:
            if not text.strip():
                errors.append("summary file is empty")

    figures_dir_value = aggregate_status.get("figures_dir")
    figures_by_id: dict[str, dict[str, object]] = {}
    indexed_image_paths: dict[str, str] = {}
    if figure_entries is not None:
        figures_by_id, indexed_image_paths, figure_errors = validate_figure_index(
            figure_entries,
            pdf_pages=pdf_pages,
        )
        errors.extend(figure_errors)

    if text is not None and text.strip() and isinstance(template, dict):
        required_headings = [
            str(section["heading"])
            for section in template.get("sections", [])
            if isinstance(section, dict) and isinstance(section.get("heading"), str)
        ]
        for heading in required_headings:
            if heading not in text:
                errors.append(f"missing heading: {heading}")
        core = template.get("core_conclusion", {})
        core_prefix = core.get("prefix") if isinstance(core, dict) else None
        if isinstance(core_prefix, str) and core_prefix not in text:
            errors.append(f"missing core conclusion block: {core_prefix}")

        if isinstance(metadata, dict):
            errors.extend(validate_metadata(text, metadata))
        if isinstance(document, dict):
            errors.extend(
                validate_evidence(
                    evidence_document,
                    template=template,
                    page_fragments=build_page_fragments(document),
                    pdf_pages=pdf_pages,
                    figures=figures_by_id,
                )
            )
        if not isinstance(figures_dir_value, str):
            errors.append("aggregate status is missing figures_dir")
        else:
            errors.extend(
                validate_images(
                    text,
                    summary_path=summary_path,
                    figures_dir=Path(figures_dir_value).expanduser().resolve(),
                    parse_dir=work_dir / "parse",
                    indexed_image_paths=indexed_image_paths,
                )
            )
        warnings.extend(wrapper_warnings(text))

    result["valid"] = not errors
    write_json(validation_path, result)

    aggregate_status["status"] = "succeeded" if result["valid"] else "failed"
    aggregate_status["step"] = None if result["valid"] else ("validate" if parse_ok else "parse")
    aggregate_status["updated_at"] = utc_now_iso()
    aggregate_status["warnings"] = list(dict.fromkeys(str(item) for item in warnings))
    aggregate_status["error"] = (
        None
        if result["valid"]
        else {
            "code": "summary_validation_failed",
            "message": "; ".join(str(item) for item in errors),
        }
    )
    write_json(status_path, aggregate_status)

    print(f"validation={validation_path}")
    print(f"status={status_path}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
