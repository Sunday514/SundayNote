#!/usr/bin/env python3
"""Rank Markdown files by header-level maintenance signals."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = [
    "last_updated",
    "update_count",
    "last_queried",
    "query_count",
    "sources",
    "topic",
    "keywords",
]
LIST_FIELDS = {"sources", "keywords"}
DATE_FIELDS = {"last_updated", "last_queried"}
COUNT_FIELDS = {"update_count", "query_count"}


@dataclass
class Issue:
    code: str
    severity: int
    detail: str


@dataclass
class FileReport:
    path: str
    priority: int
    level: str
    topic: str = ""
    last_updated: str = ""
    query_count: str = ""
    in_index: bool | None = None
    issues: list[Issue] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Markdown YAML headers and rank files for lint review."
    )
    parser.add_argument(
        "--scope",
        action="append",
        required=True,
        help="Markdown file or directory to inspect. Repeat for multiple scopes.",
    )
    parser.add_argument(
        "--index",
        action="append",
        default=[],
        help="Optional Markdown index file used to detect unindexed pages.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Root used for relative output paths.",
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        default=180,
        help="Days after last_updated that should be flagged as stale.",
    )
    parser.add_argument(
        "--high-query-count",
        type=int,
        default=5,
        help="query_count threshold for high-use maintenance checks.",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum rows to output. 0 means no limit.",
    )
    return parser.parse_args()


def markdown_files(scopes: list[str], root: Path) -> list[Path]:
    files: set[Path] = set()
    for scope in scopes:
        path = resolve_path(scope, root)
        if path.is_file() and path.suffix.lower() == ".md":
            files.add(path)
        elif path.is_dir():
            files.update(path.rglob("*.md"))
    return sorted(files)


def resolve_path(raw_path: str, root: Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_header(text: str) -> tuple[str | None, bool]:
    if not text.startswith("---\n"):
        return None, False
    end = text.find("\n---", 4)
    if end == -1:
        return None, True
    return text[4:end], False


def parse_header(header_text: str) -> dict[str, Any]:
    header: dict[str, Any] = {}
    current_list: str | None = None
    for line in header_text.splitlines():
        key_match = re.match(r"^([A-Za-z_]+):(?:\s*(.*))?$", line)
        if key_match:
            key = key_match.group(1)
            value = (key_match.group(2) or "").strip()
            current_list = None
            if key in LIST_FIELDS:
                header[key] = parse_list_value(value)
                if value == "":
                    current_list = key
            elif key in COUNT_FIELDS:
                header[key] = strip_quotes(value)
            elif key in DATE_FIELDS:
                header[key] = strip_quotes(value)
            else:
                header[key] = strip_quotes(value)
            continue
        if current_list and line.strip().startswith("- "):
            item = strip_quotes(line.strip()[2:].strip())
            if item:
                header.setdefault(current_list, []).append(item)
    return header


def parse_list_value(value: str) -> list[str]:
    value = value.strip()
    if not value or value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        items = [item.strip() for item in value[1:-1].split(",")]
        return [strip_quotes(item) for item in items if item]
    return [strip_quotes(value)]


def strip_quotes(value: str) -> str:
    return value.strip().strip("\"'")


def parse_date(value: Any) -> date | None:
    if value in {"", None}:
        return None
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_count(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"\d+", value):
        return int(value)
    return None


def wiki_links(text: str) -> set[str]:
    links: set[str] = set()
    for match in re.finditer(r"\[\[([^\]|#]+)", text):
        links.add(match.group(1).strip())
    return links


def index_links(index_paths: list[str], root: Path) -> set[str]:
    links: set[str] = set()
    for raw_path in index_paths:
        path = resolve_path(raw_path, root)
        if path.is_file():
            links.update(wiki_links(read_text(path)))
    return links


def linked_by_index(path: Path, root: Path, links: set[str]) -> bool:
    stem = path.stem
    try:
        relative_without_suffix = str(path.relative_to(root).with_suffix(""))
    except ValueError:
        relative_without_suffix = str(path.with_suffix(""))
    normalized = {link.replace("\\", "/").strip("/") for link in links}
    return stem in links or relative_without_suffix.replace("\\", "/") in normalized


def inspect_file(
    path: Path,
    root: Path,
    indexed_links: set[str] | None,
    stale_days: int,
    high_query_count: int,
    duplicate_topics: set[str],
) -> FileReport:
    relative = rel(path, root)
    text = read_text(path)
    header_text, unterminated = extract_header(text)
    issues: list[Issue] = []
    header: dict[str, Any] = {}

    if unterminated:
        issues.append(Issue("broken_header", 50, "unterminated YAML header"))
    elif header_text is None:
        issues.append(Issue("missing_header", 50, "missing YAML header"))
    else:
        header = parse_header(header_text)

    if header:
        inspect_required_fields(header, issues)
        inspect_dates(header, issues, stale_days)
        inspect_counts(header, issues)
        inspect_lists(header, issues)
        inspect_topic(header, issues, duplicate_topics)
        inspect_usage(header, issues, high_query_count)

    in_index: bool | None = None
    if indexed_links is not None:
        in_index = linked_by_index(path, root, indexed_links)
        if not in_index:
            issues.append(Issue("not_indexed", 12, "not linked from supplied index"))

    priority = sum(issue.severity for issue in issues)
    return FileReport(
        path=relative,
        priority=priority,
        level=priority_level(priority),
        topic=str(header.get("topic", "")),
        last_updated=str(header.get("last_updated", "")),
        query_count=str(header.get("query_count", "")),
        in_index=in_index,
        issues=issues,
    )


def inspect_required_fields(header: dict[str, Any], issues: list[Issue]) -> None:
    for field_name in REQUIRED_FIELDS:
        if field_name not in header:
            issues.append(Issue("missing_field", 18, f"missing {field_name}"))


def inspect_dates(header: dict[str, Any], issues: list[Issue], stale_days: int) -> None:
    today = date.today()
    for field_name in DATE_FIELDS:
        if field_name not in header:
            continue
        value = header[field_name]
        parsed = parse_date(value)
        if value == "" and field_name == "last_queried":
            continue
        if parsed is None:
            issues.append(Issue("bad_date", 16, f"{field_name} must be YYYY-MM-DD or empty last_queried"))
            continue
        if field_name == "last_updated" and (today - parsed).days > stale_days:
            issues.append(Issue("stale", 10, f"last_updated older than {stale_days} days"))


def inspect_counts(header: dict[str, Any], issues: list[Issue]) -> None:
    for field_name in COUNT_FIELDS:
        if field_name not in header:
            continue
        if parse_count(header[field_name]) is None:
            issues.append(Issue("bad_count", 16, f"{field_name} must be a non-negative integer"))


def inspect_lists(header: dict[str, Any], issues: list[Issue]) -> None:
    sources = header.get("sources") if "sources" in header else None
    keywords = header.get("keywords") if "keywords" in header else None
    if "sources" not in header and "keywords" not in header:
        return
    if not isinstance(sources, list):
        if "sources" in header:
            issues.append(Issue("bad_sources", 16, "sources must be a list"))
    elif not sources:
        issues.append(Issue("empty_sources", 14, "sources is empty"))

    if not isinstance(keywords, list):
        if "keywords" in header:
            issues.append(Issue("bad_keywords", 16, "keywords must be a list"))
    elif not keywords:
        issues.append(Issue("empty_keywords", 12, "keywords is empty"))
    elif len(keywords) > 12:
        issues.append(Issue("many_keywords", 6, "keywords has more than 12 items"))


def inspect_topic(header: dict[str, Any], issues: list[Issue], duplicate_topics: set[str]) -> None:
    if "topic" not in header:
        return
    topic = header.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        issues.append(Issue("empty_topic", 16, "topic is empty"))
        return
    if len(topic) > 40:
        issues.append(Issue("broad_topic", 8, "topic is longer than 40 characters"))
    if topic in duplicate_topics:
        issues.append(Issue("duplicate_topic", 18, "topic appears in multiple files"))
    keywords = header.get("keywords")
    if isinstance(keywords, list) and topic in keywords:
        issues.append(Issue("topic_as_keyword", 6, "topic is repeated as a keyword"))


def inspect_usage(header: dict[str, Any], issues: list[Issue], high_query_count: int) -> None:
    query_count = parse_count(header.get("query_count"))
    last_queried = header.get("last_queried")
    sources = header.get("sources")
    keywords = header.get("keywords")
    if query_count == 0 and last_queried not in {"", None}:
        issues.append(Issue("query_mismatch", 10, "last_queried is set but query_count is 0"))
    if query_count and query_count >= high_query_count:
        if not sources:
            issues.append(Issue("high_use_empty_sources", 18, "high query_count but empty sources"))
        if not keywords:
            issues.append(Issue("high_use_empty_keywords", 14, "high query_count but empty keywords"))


def duplicate_topics(files: list[Path]) -> set[str]:
    counts: dict[str, int] = {}
    for path in files:
        header_text, _unterminated = extract_header(read_text(path))
        if not header_text:
            continue
        topic = parse_header(header_text).get("topic")
        if isinstance(topic, str) and topic.strip():
            counts[topic] = counts.get(topic, 0) + 1
    return {topic for topic, count in counts.items() if count > 1}


def priority_level(priority: int) -> str:
    if priority >= 50:
        return "high"
    if priority >= 20:
        return "medium"
    if priority > 0:
        return "low"
    return "ok"


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def report_markdown(reports: list[FileReport], args: argparse.Namespace) -> None:
    print("# Lint Header Candidates\n")
    print(f"- Scope: `{', '.join(args.scope)}`")
    if args.index:
        print(f"- Index: `{', '.join(args.index)}`")
    print(f"- Files: {len(reports)}")
    print("- Body text: not inspected\n")
    print("| 优先级 | 文件 | topic | last_updated | query_count | index | 证据 |")
    print("|---|---|---|---|---|---|---|")
    for report in reports:
        index_text = "" if report.in_index is None else ("yes" if report.in_index else "no")
        evidence = "; ".join(issue.detail for issue in report.issues) or "ok"
        print(
            f"| {report.level} ({report.priority}) "
            f"| `{report.path}` "
            f"| {escape_cell(report.topic)} "
            f"| {escape_cell(report.last_updated)} "
            f"| {escape_cell(report.query_count)} "
            f"| {index_text} "
            f"| {escape_cell(evidence)} |"
        )


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def report_json(reports: list[FileReport]) -> None:
    data = [
        {
            "path": report.path,
            "priority": report.priority,
            "level": report.level,
            "topic": report.topic,
            "last_updated": report.last_updated,
            "query_count": report.query_count,
            "in_index": report.in_index,
            "issues": [issue.__dict__ for issue in report.issues],
        }
        for report in reports
    ]
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    files = markdown_files(args.scope, root)
    duplicate_topic_values = duplicate_topics(files)
    indexed_links = index_links(args.index, root) if args.index else None
    reports = [
        inspect_file(
            path=path,
            root=root,
            indexed_links=indexed_links,
            stale_days=args.stale_days,
            high_query_count=args.high_query_count,
            duplicate_topics=duplicate_topic_values,
        )
        for path in files
    ]
    reports.sort(key=lambda report: (-report.priority, report.path))
    if args.limit > 0:
        reports = reports[: args.limit]

    if args.format == "json":
        report_json(reports)
    else:
        report_markdown(reports, args)


if __name__ == "__main__":
    main()
