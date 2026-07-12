#!/usr/bin/env python3
"""Find Wiki documents relevant to literal query terms."""

from __future__ import annotations

import argparse
import ast
import re
import shutil
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

HEADER_FIELDS = {"sources", "topic", "keywords"}
LIST_FIELDS = {"sources", "keywords"}
WIKI_DIR = Path("30_知识库")
INDEX_PATH = WIKI_DIR / "索引.md"
MAINTENANCE_LOG_PATH = WIKI_DIR / "知识库维护日志.md"


@dataclass(frozen=True)
class Candidate:
    path: Path
    is_index: bool
    coverage: int
    signal_coverage: int
    score: int
    counts: Counter[str]
    header: dict[str, object]


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="+", help="Literal search terms; each argument remains one term.")
    parser.add_argument("--vault-root", default=".", help="Vault root path.")
    parser.add_argument("--limit", type=positive_int, default=10)
    return parser.parse_args()


def normalize_terms(raw_terms: list[str]) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for raw_term in raw_terms:
        term = raw_term.strip().lower()
        if term and term not in seen:
            seen.add(term)
            terms.append(term)
    if not terms:
        raise SystemExit("No search terms provided")
    return terms


def wiki_markdown_files(wiki_root: Path, maintenance_log: Path) -> list[Path]:
    files: set[Path] = set()
    for candidate in wiki_root.rglob("*.md"):
        resolved = candidate.resolve()
        if not resolved.is_file() or not resolved.is_relative_to(wiki_root):
            continue
        if resolved != maintenance_log:
            files.add(resolved)
    return sorted(files)


def rg_candidates(wiki_root: Path, files: list[Path], terms: list[str]) -> set[Path] | None:
    if not shutil.which("rg"):
        return None

    command = ["rg", "-i", "-F", "-l", "--null", "--glob", "*.md"]
    for term in terms:
        command.extend(["-e", term])
    command.extend(["--", str(wiki_root)])
    result = subprocess.run(command, capture_output=True, check=False)
    if result.returncode not in {0, 1}:
        return None

    allowed = set(files)
    candidates = {
        Path(raw_path.decode("utf-8")).resolve()
        for raw_path in result.stdout.split(b"\0")
        if raw_path
    }
    candidates &= allowed
    candidates.update(
        path for path in files if any(term in path.name.lower() for term in terms)
    )
    return candidates


def score_candidate(path: Path, terms: list[str], index: Path) -> Candidate | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    header = parse_header(text)
    filename = path.name.lower()
    haystack = f"{path.name}\n{text}".lower()
    counts = Counter({term: haystack.count(term) for term in terms})
    coverage = sum(count > 0 for count in counts.values())
    if coverage == 0:
        return None

    signal_parts = [filename, str(header.get("topic", "")).lower()]
    signal_parts.extend(str(item).lower() for item in header.get("keywords", []))
    signal_text = "\n".join(signal_parts)
    signal_coverage = sum(term in signal_text for term in terms)
    return Candidate(path, path == index, coverage, signal_coverage, sum(counts.values()), counts, header)


def parse_inline_list(value: str) -> list[str]:
    value = value.strip()
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            parsed = None
        if isinstance(parsed, list):
            return [str(item) for item in parsed if str(item).strip()]
        return [strip_quotes(item.strip()) for item in value[1:-1].split(",") if item.strip()]
    return [strip_quotes(value)] if value else []


def strip_quotes(value: str) -> str:
    return value.strip().strip("\"'")


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


def parse_header(text: str) -> dict[str, object]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return {}
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}

    header: dict[str, object] = {}
    current_list: str | None = None
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z_]+):(?:\s*(.*))?$", line)
        if match:
            key = match.group(1)
            value = strip_inline_comment(match.group(2) or "").strip()
            current_list = None
            if key not in HEADER_FIELDS:
                continue
            if key in LIST_FIELDS:
                header[key] = parse_inline_list(value)
                if not value:
                    current_list = key
            else:
                header[key] = strip_quotes(value)
            continue
        if current_list and line.strip().startswith("- "):
            item = strip_quotes(line.strip()[2:].strip())
            if item:
                header.setdefault(current_list, []).append(item)
    return header


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def display_values(values: object, limit: int) -> str:
    items = list(values) if isinstance(values, list) else [str(values)]
    displayed = ", ".join(f"`{value}`" for value in items[:limit])
    if len(items) > limit:
        displayed += f", ... (+{len(items) - limit})"
    return displayed


def main() -> int:
    args = parse_args()
    terms = normalize_terms(args.query)
    vault_root = Path(args.vault_root).resolve()
    if not vault_root.is_dir():
        raise SystemExit(f"vault root is not a directory: {vault_root}")
    wiki_root = (vault_root / WIKI_DIR).resolve()
    if not wiki_root.is_dir():
        raise SystemExit(f"fixed Wiki directory is missing: {wiki_root}")
    index_path = (vault_root / INDEX_PATH).resolve()
    maintenance_log = (vault_root / MAINTENANCE_LOG_PATH).resolve()

    files = wiki_markdown_files(wiki_root, maintenance_log)
    discovered = rg_candidates(wiki_root, files, terms)
    backend = "rg fixed-string + Python scoring"
    if discovered is None:
        discovered = set(files)
        backend = "Python literal fallback"

    candidates = [
        candidate
        for path in discovered
        if (candidate := score_candidate(path, terms, index_path))
    ]
    candidates.sort(
        key=lambda item: (
            item.is_index,
            -item.coverage,
            -item.signal_coverage,
            -item.score,
            rel(item.path, vault_root),
        )
    )

    print("# Query Candidates\n")
    print("- Scope: `wiki`")
    print(f"- Terms: `{', '.join(terms)}`")
    print(f"- Search: `{backend}`")
    print(f"- Markdown files in scope: {len(files)}")
    print(f"- Scored candidates: {len(candidates)}\n")

    if not candidates:
        print("No matching Wiki pages found. This is a Wiki coverage gap.")
        return 0

    print("## Files\n")
    for index, candidate in enumerate(candidates[: args.limit], start=1):
        count_text = ", ".join(
            f"{term}:{candidate.counts[term]}" for term in terms if candidate.counts[term]
        )
        print(
            f"{index}. `{rel(candidate.path, vault_root)}` "
            f"coverage={candidate.coverage}/{len(terms)} "
            f"signal={candidate.signal_coverage} score={candidate.score}"
        )
        print(f"   - matched: {count_text}")
        topic = candidate.header.get("topic")
        if topic:
            print(f"   - topic: {topic}")
        for key in ("keywords", "sources"):
            values = candidate.header.get(key)
            if values:
                limit = 8 if key == "keywords" else 5
                print(f"   - {key}: {display_values(values, limit)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
