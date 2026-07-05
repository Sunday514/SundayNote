#!/usr/bin/env python3
"""Audit Markdown reachability from an entry page.

This script checks whether Markdown files in selected scopes are reachable
through Obsidian-style wikilinks or Markdown links from an entry document.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


WIKILINK_RE = re.compile(r"!??\[\[([^\]]+)\]\]")
MD_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
IGNORED_UNRESOLVED_SUFFIXES = (
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".pdf",
    ".docx",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry", required=True, help="Entry Markdown file.")
    parser.add_argument("--scope", action="append", required=True, help="Markdown file or directory to audit. Repeatable.")
    parser.add_argument("--include-file", action="append", default=[], help="Extra Markdown files to include in link resolution.")
    parser.add_argument("--root", default=".", help="Vault root for relative paths.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    entry = (root / args.entry).resolve()
    if not entry.is_file():
        parser.error(f"--entry not found or not a file: {args.entry}")
    files = collect_files(root, args.scope, args.include_file)
    files.add(entry)

    by_rel = {rel(root, path): path for path in files}
    by_rel_no_ext = {rel(root, path.with_suffix("")): path for path in files}
    by_abs = {path.resolve(): path for path in files}
    by_name: dict[str, list[Path]] = {}
    for path in files:
        by_name.setdefault(path.stem, []).append(path)

    graph = {path: set() for path in files}
    backlinks = {path: set() for path in files}
    ambiguous = []
    unresolved = []

    for path in files:
        text = path.read_text(encoding="utf-8")
        for match in WIKILINK_RE.finditer(text):
            raw = match.group(1)
            target = strip_wikilink(raw)
            ambiguous_link = False
            if "/" not in target and target:
                matches = by_name.get(Path(target).stem, [])
                if len(matches) > 1:
                    ambiguous.append({
                        "source": rel(root, path),
                        "link": raw,
                        "candidates": [rel(root, item) for item in matches],
                    })
                    ambiguous_link = True
            if ambiguous_link:
                continue
            resolved = resolve(target, path, by_rel, by_rel_no_ext, by_abs, by_name)
            if resolved:
                graph[path].add(resolved)
                backlinks[resolved].add(path)
            elif should_report_unresolved(target):
                unresolved.append({"source": rel(root, path), "link": raw})

        for match in MD_LINK_RE.finditer(text):
            target = strip_markdown_link(match.group(1))
            resolved = resolve(target, path, by_rel, by_rel_no_ext, by_abs, by_name)
            if resolved:
                graph[path].add(resolved)
                backlinks[resolved].add(path)
            elif should_report_unresolved(target):
                unresolved.append({"source": rel(root, path), "link": target})

    seen = reachable(entry, graph)
    not_reachable = sorted(rel(root, path) for path in files if path not in seen)
    zero_inlinks = sorted(rel(root, path) for path in files if path != entry and not backlinks[path])

    report = {
        "entry": rel(root, entry),
        "total": len(files),
        "reachable": len(seen),
        "not_reachable_count": len(not_reachable),
        "not_reachable": not_reachable,
        "zero_inlinks_count": len(zero_inlinks),
        "zero_inlinks": zero_inlinks,
        "ambiguous_count": len(ambiguous),
        "ambiguous": ambiguous,
        "unresolved_count": len(unresolved),
        "unresolved": unresolved,
    }

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_markdown(report)
    return 0 if not not_reachable and not ambiguous else 1


def collect_files(root: Path, scopes: Iterable[str], include_files: Iterable[str]) -> set[Path]:
    files: set[Path] = set()
    for scope in scopes:
        path = root / scope
        if path.is_file() and path.suffix == ".md":
            files.add(path.resolve())
        elif path.is_dir():
            files.update(item.resolve() for item in path.rglob("*.md"))
    for item in include_files:
        path = root / item
        if path.is_file() and path.suffix == ".md":
            files.add(path.resolve())
    return files


def strip_wikilink(raw: str) -> str:
    return raw.split("|", 1)[0].split("#", 1)[0].strip().lstrip("./")


def strip_markdown_link(raw: str) -> str:
    return raw.strip().replace("%20", " ").split("#", 1)[0].lstrip("./")


def resolve(
    target: str,
    source: Path,
    by_rel: dict[str, Path],
    by_rel_no_ext: dict[str, Path],
    by_abs: dict[Path, Path],
    by_name: dict[str, list[Path]],
) -> Path | None:
    if not target or target.startswith(("http://", "https://", "obsidian://", "mailto:")):
        return None

    candidates = [target] if target.endswith(".md") else [f"{target}.md", target]
    for candidate in candidates:
        if candidate in by_rel:
            return by_rel[candidate]
        if candidate in by_rel_no_ext:
            return by_rel_no_ext[candidate]

    for candidate in candidates:
        relative = (source.parent / candidate).resolve()
        if relative in by_abs:
            return by_abs[relative]
        if relative.with_suffix("") in by_abs:
            return by_abs[relative.with_suffix("")]

    if "/" not in target:
        matches = by_name.get(Path(target).stem, [])
        if len(matches) == 1:
            return matches[0]
    return None


def should_report_unresolved(target: str) -> bool:
    if not target or target.startswith("Pasted image"):
        return False
    if target.startswith(("http://", "https://", "obsidian://", "mailto:")):
        return False
    lowered = target.lower()
    return not lowered.endswith(IGNORED_UNRESOLVED_SUFFIXES)


def reachable(entry: Path, graph: dict[Path, set[Path]]) -> set[Path]:
    if entry not in graph:
        return set()
    seen = {entry}
    stack = [entry]
    while stack:
        path = stack.pop()
        for target in graph.get(path, set()):
            if target not in seen:
                seen.add(target)
                stack.append(target)
    return seen


def rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def print_markdown(report: dict) -> None:
    print("# Reachability Audit")
    print()
    print(f"- Entry: `{report['entry']}`")
    print(f"- Reachable: {report['reachable']} / {report['total']}")
    print(f"- Not reachable: {report['not_reachable_count']}")
    print(f"- Zero inlinks: {report['zero_inlinks_count']}")
    print(f"- Ambiguous links: {report['ambiguous_count']}")
    print(f"- Unresolved links: {report['unresolved_count']}")
    print()
    for key, heading in (
        ("not_reachable", "Not Reachable"),
        ("zero_inlinks", "Zero Inlinks"),
        ("ambiguous", "Ambiguous Links"),
        ("unresolved", "Unresolved Links"),
    ):
        if not report[key]:
            continue
        print(f"## {heading}")
        for item in report[key][:100]:
            print(f"- `{item}`" if isinstance(item, str) else f"- `{item}`")
        if len(report[key]) > 100:
            print(f"- ... {len(report[key]) - 100} more")
        print()


if __name__ == "__main__":
    raise SystemExit(main())
