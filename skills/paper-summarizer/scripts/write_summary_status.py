#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate one paper summary status.")
    parser.add_argument("summary", type=Path, help="Path to the Raw summary Markdown")
    parser.add_argument("--work-dir", type=Path, required=True, help="Import workspace _work directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary_path = args.summary.expanduser().resolve()
    work_dir = args.work_dir.expanduser().resolve()
    parse_status_path = work_dir / "parse" / "status.json"
    validation_path = work_dir / "summarize" / "validation.json"
    status_path = work_dir / "status.json"

    status = "succeeded"
    step = None
    error = None
    if not parse_status_path.exists() or read_json(parse_status_path).get("ok") is not True:
        status = "failed"
        step = "parse"
        error = "parse status missing or failed"
    elif not summary_path.exists():
        status = "pending"
        step = "summarize"
        error = "summary not written"
    elif not validation_path.exists() or read_json(validation_path).get("valid") is not True:
        status = "failed"
        step = "validate"
        error = "validation missing or failed"

    payload = {
        "status": status,
        "step": step,
        "summary_path": str(summary_path),
        "updated_at": utc_now_iso(),
        "error": {"message": error} if error else None,
    }
    write_json(status_path, payload)
    print(f"status={status_path}")
    return 0 if status == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
