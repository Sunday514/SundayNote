#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE_PATH = SKILL_DIR / "assets" / "summary_template.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a markdown paper summary against the bundled template."
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

    result: dict[str, object] = {
        "summary_path": str(summary_path),
        "template_path": str(template_path),
        "valid": False,
        "missing_headings": [],
        "missing_header_fields": [],
        "errors": [],
    }
    errors = result["errors"]
    if not isinstance(errors, list):
        raise TypeError("errors field must be a list")
    if not template_path.exists():
        errors.append("summary_template.json not found")
    if not summary_path.exists():
        errors.append("summary file not found")
    if errors:
        validation_path.parent.mkdir(parents=True, exist_ok=True)
        validation_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"validation={validation_path}")
        return 1

    config = json.loads(template_path.read_text(encoding="utf-8"))
    text = summary_path.read_text(encoding="utf-8")
    required_headings = ["# "]
    for section in config.get("sections", []):
        if isinstance(section, dict) and isinstance(section.get("heading"), str):
            required_headings.append(str(section["heading"]))
    core_conclusion = config.get("core_conclusion", {})
    core_conclusion_prefix = core_conclusion.get("prefix") if isinstance(core_conclusion, dict) else None
    required_header_fields = [f"- {item}：" for item in config.get("header_fields", [])]

    missing_headings = result["missing_headings"]
    missing_header_fields = result["missing_header_fields"]
    if not isinstance(missing_headings, list) or not isinstance(missing_header_fields, list):
        raise TypeError("missing fields must be lists")

    for heading in required_headings:
        if heading not in text:
            missing_headings.append(heading)
    for field in required_header_fields:
        if field not in text:
            missing_header_fields.append(field)
    if isinstance(core_conclusion_prefix, str) and core_conclusion_prefix not in text:
        errors.append(f"missing core conclusion block: {core_conclusion_prefix}")

    result["valid"] = not missing_headings and not missing_header_fields and not errors
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    validation_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"validation={validation_path}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
