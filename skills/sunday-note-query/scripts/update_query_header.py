#!/usr/bin/env python3
"""Update Wiki query usage fields in Markdown YAML headers."""

from __future__ import annotations

import argparse
import re
from datetime import date, datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Increment query_count and set last_queried for used Wiki files."
    )
    parser.add_argument("paths", nargs="+", help="Wiki Markdown files actually used as evidence.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Query date in YYYY-MM-DD.")
    parser.add_argument("--root", default=".", help="Root used for relative output paths.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    query_date = parse_date(args.date)
    root = Path(args.root).resolve()
    paths = unique_paths(args.paths, root)

    for path in paths:
        update_file(path, root, query_date)
    return 0


def unique_paths(raw_paths: list[str], root: Path) -> list[Path]:
    seen: set[Path] = set()
    paths: list[Path] = []
    for raw_path in raw_paths:
        path = Path(raw_path)
        if not path.is_absolute():
            path = root / path
        path = path.resolve()
        if path not in seen:
            seen.add(path)
            paths.append(path)
    return paths


def parse_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise SystemExit(f"--date must be YYYY-MM-DD: {value}") from exc


def update_file(path: Path, root: Path, query_date: str) -> None:
    if not path.is_file() or path.suffix.lower() != ".md":
        raise SystemExit(f"not a Markdown file: {path}")

    text = path.read_text(encoding="utf-8")
    header, body = split_header(text, path)
    lines = header.splitlines()
    count_index = find_field(lines, "query_count", path)
    queried_index = find_field(lines, "last_queried", path)
    old_count = parse_count(field_value(lines[count_index]), path)

    lines[queried_index] = f"last_queried: {query_date}"
    lines[count_index] = f"query_count: {old_count + 1}"
    path.write_text("---\n" + "\n".join(lines) + "\n---" + body, encoding="utf-8")
    print(f"updated: {rel(path, root)} query_count {old_count}->{old_count + 1}")


def split_header(text: str, path: Path) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise SystemExit(f"missing YAML header: {path}")
    end = text.find("\n---", 4)
    if end == -1:
        raise SystemExit(f"unterminated YAML header: {path}")
    return text[4:end], text[end + 4 :]


def find_field(lines: list[str], field_name: str, path: Path) -> int:
    pattern = re.compile(rf"^{re.escape(field_name)}\s*:")
    matches = [index for index, line in enumerate(lines) if pattern.match(line)]
    if not matches:
        raise SystemExit(f"missing {field_name}: {path}")
    if len(matches) > 1:
        raise SystemExit(f"duplicate {field_name}: {path}")
    return matches[0]


def field_value(line: str) -> str:
    return line.split(":", 1)[1].strip().strip("\"'")


def parse_count(value: str, path: Path) -> int:
    if not re.fullmatch(r"\d+", value):
        raise SystemExit(f"query_count must be a non-negative integer: {path}")
    return int(value)


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
