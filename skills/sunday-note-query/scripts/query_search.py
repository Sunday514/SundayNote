#!/usr/bin/env python3
"""Find Sunday Note vault documents relevant to a query.

This helper is intentionally small: it discovers candidate Markdown files from
configured vault layers and prints link hints. It does not summarize or write.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path


WIKILINK_RE = re.compile(r"\[\[([^\]#|]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="+", help="Search terms")
    parser.add_argument("--vault-root", default=".", help="Vault root path")
    parser.add_argument(
        "--layers",
        default="wiki,schema",
        help="Comma-separated layers: wiki,schema,routine,raw,journal",
    )
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--link-limit", type=int, default=3)
    return parser.parse_args()


def find_config(vault_root: Path) -> Path:
    candidates = [
        vault_root / ".sunday-note-agent/config/sunday-note-vault.yaml",
        vault_root / "SundayNoteAgent/config/sunday-note-vault.yaml",
        vault_root / "config/sunday-note-vault.yaml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise SystemExit("No sunday-note-vault.yaml found")


def read_config_paths(config_path: Path) -> dict[str, list[str]]:
    paths: dict[str, list[str]] = {
        "raw": [],
        "routine": [],
        "wiki": [],
        "journal": [],
        "schema": [],
    }
    section_stack: list[tuple[int, str]] = []
    for line in config_path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^(\s*)([A-Za-z_]+):(?:\s+\"([^\"]+)\")?", line)
        if not match:
            continue
        indent = len(match.group(1))
        key = match.group(2)
        value = match.group(3)
        while section_stack and section_stack[-1][0] >= indent:
            section_stack.pop()
        parent = section_stack[-1][1] if section_stack else ""
        if value:
            if parent == "layers" and key in {"raw", "wiki", "journal"}:
                paths[key].append(value)
            elif parent == "routine":
                paths["routine"].append(value)
            elif parent == "schema":
                paths["schema"].append(value)
            elif parent == "wiki" and key == "index":
                paths["wiki"].append(value)
        else:
            section_stack.append((indent, key))
    return paths


def configured_path(vault_root: Path, raw_path: str) -> Path:
    path = vault_root / raw_path
    if path.exists():
        return path
    agent_prefix = f"{vault_root.name}/"
    if raw_path.startswith(agent_prefix):
        local_path = vault_root / raw_path[len(agent_prefix) :]
        if local_path.exists():
            return local_path
    return path


def markdown_files(vault_root: Path, paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw_path in paths:
        path = configured_path(vault_root, raw_path)
        if path.is_file() and path.suffix.lower() == ".md":
            files.append(path)
        elif path.is_dir():
            files.extend(path.rglob("*.md"))
    return sorted(set(files))


def score_file(path: Path, terms: list[str]) -> tuple[int, Counter[str], str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    haystack = f"{path.name}\n{text}".lower()
    counts = Counter({term: haystack.count(term) for term in terms})
    score = sum(counts.values())
    return score, counts, text


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def main() -> None:
    args = parse_args()
    vault_root = Path(args.vault_root).resolve()
    config_path = find_config(vault_root)
    paths = read_config_paths(config_path)
    requested_layers = [layer.strip() for layer in args.layers.split(",") if layer.strip()]
    terms = [term.lower() for term in " ".join(args.query).split() if term.strip()]

    scoped_paths: list[str] = []
    for layer in requested_layers:
        scoped_paths.extend(paths.get(layer, []))

    files = markdown_files(vault_root, scoped_paths)
    scored: list[tuple[int, Path, Counter[str], str]] = []
    all_text: dict[Path, str] = {}
    for path in files:
        score, counts, text = score_file(path, terms)
        all_text[path] = text
        if score > 0:
            scored.append((score, path, counts, text))
    scored.sort(key=lambda item: (-item[0], rel(item[1], vault_root)))

    print(f"# Query Search\n")
    print(f"- Config: `{rel(config_path, vault_root)}`")
    print(f"- Layers: `{', '.join(requested_layers)}`")
    print(f"- Terms: `{', '.join(terms)}`")
    print(f"- Markdown files scanned: {len(files)}\n")

    if not scored:
        print("No matching Markdown files found in the requested layers.")
        return

    print("## Candidates\n")
    top = scored[: args.limit]
    for score, path, counts, _text in top:
        count_text = ", ".join(f"{term}:{count}" for term, count in counts.items() if count)
        print(f"- `{rel(path, vault_root)}` score={score} ({count_text})")

    print("\n## Link Hints\n")
    by_stem = {path.stem: path for path in files}
    for _score, path, _counts, text in top[: args.link_limit]:
        links = sorted(set(WIKILINK_RE.findall(text)))[: args.link_limit]
        linked_files = [by_stem[link] for link in links if link in by_stem]
        backlinks = [
            source
            for source, source_text in all_text.items()
            if source != path and f"[[{path.stem}" in source_text
        ][: args.link_limit]
        if not linked_files and not backlinks:
            continue
        print(f"- `{rel(path, vault_root)}`")
        if linked_files:
            print(
                "  - outgoing: "
                + ", ".join(f"`{rel(link, vault_root)}`" for link in linked_files)
            )
        if backlinks:
            print(
                "  - backlinks: "
                + ", ".join(f"`{rel(link, vault_root)}`" for link in backlinks)
            )


if __name__ == "__main__":
    main()
