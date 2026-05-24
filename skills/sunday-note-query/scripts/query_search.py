#!/usr/bin/env python3
"""Find Routine and Wiki documents relevant to a query."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path


HEADER_FIELDS = {
    "last_updated",
    "update_count",
    "last_queried",
    "query_count",
    "sources",
    "topic",
    "keywords",
}
LIST_FIELDS = {"sources", "keywords"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="+", help="Search terms")
    parser.add_argument("--vault-root", default=".", help="Vault root path")
    parser.add_argument("--limit", type=int, default=10)
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


def rg_scores(paths: list[Path], terms: list[str]) -> list[tuple[int, Path]] | None:
    if not shutil.which("rg"):
        return None
    existing_paths = [path for path in paths if path.exists()]
    if not existing_paths:
        return []
    command = ["rg", "-i", "--count-matches", "--with-filename", "--glob", "*.md"]
    for term in terms:
        command.extend(["-e", term])
    command.extend(str(path) for path in existing_paths)
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode not in {0, 1}:
        return None
    scores: dict[Path, int] = {}
    for line in result.stdout.splitlines():
        if ":" not in line:
            continue
        path_text, score_text = line.rsplit(":", 1)
        try:
            score = int(score_text)
        except ValueError:
            continue
        path = Path(path_text).resolve()
        scores[path] = max(scores.get(path, 0), score)
    return [(score, path) for path, score in scores.items()]


def with_filename_scores(scored: list[tuple[int, Path]], files: list[Path], terms: list[str]) -> list[tuple[int, Path]]:
    scores = {path.resolve(): score for score, path in scored}
    for path in files:
        name = path.name.lower()
        score = sum(name.count(term) for term in terms)
        if score > 0:
            resolved = path.resolve()
            scores[resolved] = scores.get(resolved, 0) + score
    return [(score, path) for path, score in scores.items()]


def search_roots(vault_root: Path, paths: list[str]) -> list[Path]:
    roots = sorted({configured_path(vault_root, raw_path).resolve() for raw_path in paths})
    directories = [path for path in roots if path.is_dir()]
    return [
        path
        for path in roots
        if not any(path != directory and path.is_relative_to(directory) for directory in directories)
    ]


def score_text(path: Path, terms: list[str]) -> tuple[Counter[str], str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    haystack = f"{path.name}\n{text}".lower()
    counts = Counter({term: haystack.count(term) for term in terms})
    return counts, text


def python_scores(files: list[Path], terms: list[str]) -> list[tuple[int, Path]]:
    scores: list[tuple[int, Path]] = []
    for path in files:
        counts, _text = score_text(path, terms)
        score = sum(counts.values())
        if score > 0:
            scores.append((score, path))
    return scores


def parse_inline_list(value: str) -> list[str]:
    value = value.strip()
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        raw_items = [item.strip() for item in value[1:-1].split(",")]
        return [strip_quotes(item) for item in raw_items if item]
    return [strip_quotes(value)] if value else []


def strip_quotes(value: str) -> str:
    return value.strip().strip("\"'")


def parse_header(text: str) -> dict[str, object]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    header: dict[str, object] = {}
    current_list: str | None = None
    for line in text[4:end].splitlines():
        key_match = re.match(r"^([A-Za-z_]+):(?:\s*(.*))?$", line)
        if key_match:
            key = key_match.group(1)
            value = (key_match.group(2) or "").strip()
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


def layer_root(path: Path, vault_root: Path) -> str:
    try:
        return path.relative_to(vault_root).parts[0]
    except (ValueError, IndexError):
        return path.parent.name


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
    terms = [term.lower() for term in " ".join(args.query).split() if term.strip()]
    if not terms:
        raise SystemExit("No search terms provided")

    scoped_paths = paths["wiki"] + paths["routine"]

    files = markdown_files(vault_root, scoped_paths)
    scoped_roots = search_roots(vault_root, scoped_paths)
    scored = rg_scores(scoped_roots, terms)
    search = "rg count-matches"
    if scored is None:
        scored = python_scores(files, terms)
        search = "python full text"
    else:
        scored = with_filename_scores(scored, files, terms)
        search = "rg count-matches + filename"
    scored.sort(key=lambda item: (-item[0], rel(item[1], vault_root)))

    print("# Query Candidates\n")
    print("- Scope: `wiki,routine`")
    print(f"- Terms: `{', '.join(terms)}`")
    print(f"- Search: `{search}`")
    print(f"- Markdown files in scope: {len(files)}\n")

    if not scored:
        print("No matching Markdown files found in Wiki/Routine.")
        return

    print("## Files\n")
    top = scored[: args.limit]
    for index, (score, path) in enumerate(top, start=1):
        counts, text = score_text(path, terms)
        count_text = ", ".join(f"{term}:{count}" for term, count in counts.items() if count)
        header = parse_header(text)
        root = layer_root(path, vault_root)
        print(f"{index}. `{rel(path, vault_root)}` score={score} root=`{root}`")
        if count_text:
            print(f"   - matched: {count_text}")
        if header:
            fields = [
                f"{key}={header[key]!r}"
                for key in ["last_updated", "update_count", "last_queried", "query_count", "topic"]
                if key in header
            ]
            if fields:
                print("   - header: " + ", ".join(fields))
            for key in ["keywords", "sources"]:
                values = header.get(key)
                if values:
                    print("   - " + key + ": " + ", ".join(f"`{value}`" for value in values))
        else:
            print(f"   - no header: title=`{path.stem}`")


if __name__ == "__main__":
    main()
