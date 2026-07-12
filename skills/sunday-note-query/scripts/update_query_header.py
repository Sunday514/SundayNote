#!/usr/bin/env python3
"""Update usage fields for Wiki pages actually used by Query."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

WIKI_DIR = Path("30_知识库")
MAINTENANCE_LOG_PATH = WIKI_DIR / "知识库维护日志.md"
@dataclass(frozen=True)
class PreparedUpdate:
    path: Path
    text: str
    old_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Wiki Markdown files actually used as evidence.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Query date in YYYY-MM-DD.")
    parser.add_argument(
        "--vault-root",
        "--root",
        dest="vault_root",
        default=".",
        help="Vault root containing the fixed Sunday Note layout.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    query_date = parse_date(args.date, "--date")
    vault_root = Path(args.vault_root).resolve()
    if not vault_root.is_dir():
        raise SystemExit(f"vault root is not a directory: {vault_root}")
    wiki_root = (vault_root / WIKI_DIR).resolve()
    if not wiki_root.is_dir():
        raise SystemExit(f"fixed Wiki directory is missing: {wiki_root}")
    maintenance_log = (vault_root / MAINTENANCE_LOG_PATH).resolve()

    targets = unique_targets(args.paths, vault_root, wiki_root, maintenance_log)
    prepared = [prepare_update(path, query_date) for path in targets]

    for update in prepared:
        with update.path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(update.text)
        print(
            f"updated: {rel(update.path, vault_root)} "
            f"query_count {update.old_count}->{update.old_count + 1}"
        )
    return 0


def unique_targets(
    raw_paths: list[str],
    vault_root: Path,
    wiki_root: Path,
    maintenance_log: Path,
) -> list[Path]:
    targets: list[Path] = []
    seen: set[Path] = set()
    for raw_path in raw_paths:
        target = Path(raw_path)
        if not target.is_absolute():
            target = vault_root / target
        target = target.resolve()
        if not target.is_relative_to(wiki_root):
            raise SystemExit(f"not inside fixed Wiki: {target}")
        if target == maintenance_log:
            raise SystemExit(f"maintenance log is not Query evidence: {target}")
        if not target.is_file() or target.suffix.lower() != ".md":
            raise SystemExit(f"not a Wiki Markdown file: {target}")
        if target not in seen:
            seen.add(target)
            targets.append(target)
    return targets


def prepare_update(path: Path, query_date: str) -> PreparedUpdate:
    with path.open("r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    lines = text.splitlines(keepends=True)
    header_end = find_header_end(lines, path)
    queried_index = find_field(lines, 1, header_end, "last_queried", path)
    count_index = find_field(lines, 1, header_end, "query_count", path)

    old_queried = field_value(lines[queried_index])
    if old_queried:
        parse_date(old_queried, "last_queried", path)
    old_count = parse_count(field_value(lines[count_index]), path)

    lines[queried_index] = replace_field_value(lines[queried_index], "last_queried", query_date)
    lines[count_index] = replace_field_value(lines[count_index], "query_count", str(old_count + 1))
    return PreparedUpdate(path, "".join(lines), old_count)


def find_header_end(lines: list[str], path: Path) -> int:
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise SystemExit(f"missing YAML header: {path}")
    for index in range(1, len(lines)):
        if lines[index].rstrip("\r\n") == "---":
            return index
    raise SystemExit(f"unterminated YAML header: {path}")


def find_field(lines: list[str], start: int, end: int, field_name: str, path: Path) -> int:
    pattern = re.compile(rf"^\s*{re.escape(field_name)}\s*:")
    matches = [index for index in range(start, end) if pattern.match(lines[index])]
    if not matches:
        raise SystemExit(f"missing {field_name}: {path}")
    if len(matches) > 1:
        raise SystemExit(f"duplicate {field_name}: {path}")
    return matches[0]


def field_value(line: str) -> str:
    content = line.rstrip("\r\n").split(":", 1)[1]
    return strip_inline_comment(content).strip().strip("\"'")


def strip_inline_comment(value: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote == '"':
            escaped = True
            continue
        if char in {"\"", "'"}:
            quote = None if quote == char else (char if quote is None else quote)
            continue
        if char == "#" and quote is None and (index == 0 or value[index - 1].isspace()):
            return value[:index]
    return value


def replace_field_value(line: str, field_name: str, new_value: str) -> str:
    newline = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
    content = line[: -len(newline)] if newline else line
    match = re.match(rf"^(\s*{re.escape(field_name)}\s*:\s*)(.*)$", content)
    if not match:
        raise AssertionError(f"field disappeared during update: {field_name}")

    old_value = match.group(2)
    comment_start = inline_comment_start(old_value)
    suffix = ""
    if comment_start is not None:
        value_part = old_value[:comment_start]
        suffix = value_part[len(value_part.rstrip()) :] + old_value[comment_start:]
        if comment_start == 0:
            suffix = " " + suffix
    return f"{match.group(1)}{new_value}{suffix}{newline}"


def inline_comment_start(value: str) -> int | None:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote == '"':
            escaped = True
            continue
        if char in {"\"", "'"}:
            quote = None if quote == char else (char if quote is None else quote)
            continue
        if char == "#" and quote is None and (index == 0 or value[index - 1].isspace()):
            return index
    return None


def parse_date(value: str, label: str, path: Path | None = None) -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        location = f": {path}" if path else ""
        raise SystemExit(f"{label} must be YYYY-MM-DD{location}") from exc


def parse_count(value: str, path: Path) -> int:
    if not re.fullmatch(r"\d+", value):
        raise SystemExit(f"query_count must be a non-negative integer: {path}")
    return int(value)


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
