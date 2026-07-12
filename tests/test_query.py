#!/usr/bin/env python3
"""Dependency-free fixtures for Query search and usage updates."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "skills/sunday-note-query/scripts/query_search.py"
UPDATE = ROOT / "skills/sunday-note-query/scripts/update_query_header.py"


def command(*args: str, path: str | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    if path is not None:
        env["PATH"] = path
    return subprocess.run(
        [sys.executable, *args],
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def run(*args: str, path: str | None = None) -> str:
    return command(*args, path=path).stdout


def run_fail(*args: str) -> None:
    result = command(*args, check=False)
    assert result.returncode != 0, f"command unexpectedly succeeded: {args}"


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }


def wiki_header(
    topic: str,
    *,
    last_queried: str = '""',
    query_count: str = "0",
    sources: str = '["fixture"]',
    keywords: str = '["fixture"]',
) -> str:
    return f"""---
last_updated: 2026-07-12
update_count: 1
last_queried: {last_queried}
query_count: {query_count}
sources: {sources}
topic: {topic}
keywords: {keywords}
---
"""


def candidate_rows(output: str) -> list[tuple[str, int, int, int]]:
    rows = []
    pattern = re.compile(r"^\d+\. `([^`]+)` coverage=(\d+)/\d+ signal=(\d+) score=(\d+)$")
    for line in output.splitlines():
        match = pattern.match(line)
        if match:
            rows.append((match.group(1), int(match.group(2)), int(match.group(3)), int(match.group(4))))
    return rows


def test_literal_search() -> None:
    with tempfile.TemporaryDirectory() as temp:
        vault = Path(temp)
        for relative in ("30_知识库", "20_每日记录", "10_原始材料", "outside"):
            (vault / relative).mkdir()

        (vault / "30_知识库/C++ 与 .NET.md").write_bytes(
            (
                wiki_header('"C++ 与 .NET"', keywords='["C++", ".NET", "符号 ["]')
                + "\nC++ 可与 .NET 配合，字面符号 [ 应保持原样。\n"
            ).replace("\n", "\r\n").encode("utf-8")
        )
        (vault / "30_知识库/完整短语.md").write_text(
            wiki_header('"World Model"', keywords='["world model"]') + "\nworld model 是完整短语。\n",
            encoding="utf-8",
        )
        (vault / "30_知识库/拆词噪声.md").write_text(
            wiki_header('"英文拆词噪声"') + "\nworld 出现在这里，model 出现在另一处。\n",
            encoding="utf-8",
        )
        (vault / "30_知识库/多词覆盖.md").write_text(
            wiki_header('"机器人控制"', keywords='["机器人", "控制"]') + "\n机器人需要可靠控制。\n",
            encoding="utf-8",
        )
        (vault / "30_知识库/单词重复.md").write_text(
            wiki_header('"机器人重复"', keywords='["机器人"]') + ("\n机器人" * 20) + "\n",
            encoding="utf-8",
        )
        (vault / "30_知识库/独特项目.md").write_text(wiki_header('"无正文命中"') + "\n内容。\n", encoding="utf-8")
        (vault / "30_知识库/索引.md").write_text(
            wiki_header('"索引"') + "\n机器人控制导航入口词，机器人控制机器人控制。\n",
            encoding="utf-8",
        )
        (vault / "30_知识库/知识库维护日志.md").write_text("C++ 机器人控制\n", encoding="utf-8")
        (vault / "20_每日记录/2026-07-12.md").write_text("C++ 机器人控制\n", encoding="utf-8")
        (vault / "10_原始材料/来源.md").write_text("world model\n", encoding="utf-8")
        outside = vault / "outside/越界.md"
        outside.write_text("C++ 机器人控制\n", encoding="utf-8")
        try:
            (vault / "30_知识库/越界链接.md").symlink_to(outside)
        except OSError:
            pass

        before = snapshot(vault)

        symbols = run(str(QUERY), "C++", ".NET", "[", "--vault-root", str(vault))
        symbol_rows = candidate_rows(symbols)
        assert symbol_rows[0][0] == "30_知识库/C++ 与 .NET.md"
        assert symbol_rows[0][1:3] == (3, 3)
        assert "20_每日记录" not in symbols
        assert "10_原始材料" not in symbols
        assert "知识库维护日志" not in symbols
        assert "越界链接" not in symbols

        phrase = run(str(QUERY), "world model", "--vault-root", str(vault))
        assert [row[0] for row in candidate_rows(phrase)] == ["30_知识库/完整短语.md"]

        ranked = run(str(QUERY), "机器人", "控制", "--vault-root", str(vault))
        ranked_rows = candidate_rows(ranked)
        assert ranked_rows[0][0] == "30_知识库/多词覆盖.md"
        assert ranked_rows[0][1] == 2
        assert ranked_rows[1][0] == "30_知识库/单词重复.md"
        assert ranked_rows[-1][0] == "30_知识库/索引.md"

        filename = run(str(QUERY), "独特项目", "--vault-root", str(vault))
        assert candidate_rows(filename)[0][0] == "30_知识库/独特项目.md"

        duplicate = run(str(QUERY), "C++", "c++", " C++ ", "--vault-root", str(vault))
        assert "- Terms: `c++`" in duplicate
        assert "coverage=1/1" in duplicate

        index = run(str(QUERY), "导航入口词", "--vault-root", str(vault))
        assert candidate_rows(index)[0][0] == "30_知识库/索引.md"

        missing = run(str(QUERY), "不存在的精确查询词", "--vault-root", str(vault))
        assert "Wiki coverage gap" in missing
        assert not candidate_rows(missing)

        fallback = run(str(QUERY), "机器人", "控制", "--vault-root", str(vault), path="")
        assert candidate_rows(fallback) == ranked_rows
        assert snapshot(vault) == before, "Query search must not modify the vault"


def test_usage_updates() -> None:
    with tempfile.TemporaryDirectory() as temp:
        vault = Path(temp)
        for relative in ("30_知识库", "20_每日记录", "10_原始材料", "SundayNoteAgent"):
            (vault / relative).mkdir()

        page_a = vault / "30_知识库/A.md"
        page_b = vault / "30_知识库/B.md"
        page_a.write_text(
            wiki_header('"A"', last_queried='"" # keep queried comment', query_count="2 # keep count comment")
            + "\nA body must stay unchanged.\n",
            encoding="utf-8",
        )
        page_b.write_bytes(
            (wiki_header('"B"').replace('last_queried: ""', "last_queried: # blank comment") + "\nB body.\n")
            .replace("\n", "\r\n")
            .encode("utf-8")
        )
        maintenance = vault / "30_知识库/知识库维护日志.md"
        maintenance.write_text(wiki_header('"维护日志"') + "\nlog\n", encoding="utf-8")
        routine = vault / "20_每日记录/2026-07-12.md"
        routine.write_text(wiki_header('"Routine"') + "\nroutine\n", encoding="utf-8")
        raw = vault / "10_原始材料/来源.md"
        raw.write_text(wiki_header('"Raw"') + "\nraw\n", encoding="utf-8")
        schema = vault / "SundayNoteAgent/schema.md"
        schema.write_text(wiki_header('"Schema"') + "\nschema\n", encoding="utf-8")

        output = run(
            str(UPDATE),
            "30_知识库/A.md",
            "30_知识库/A.md",
            "30_知识库/B.md",
            "--vault-root",
            str(vault),
            "--date",
            "2026-07-13",
        )
        assert output.count("updated:") == 2
        text_a = page_a.read_text(encoding="utf-8")
        assert "last_queried: 2026-07-13 # keep queried comment" in text_a
        assert "query_count: 3 # keep count comment" in text_a
        assert "A body must stay unchanged." in text_a
        assert "query_count: 1" in page_b.read_text(encoding="utf-8")
        assert "last_queried: 2026-07-13 # blank comment" in page_b.read_text(encoding="utf-8")
        assert b"\r\n" in page_b.read_bytes() and b"\n" not in page_b.read_bytes().replace(b"\r\n", b"")

        run(str(UPDATE), "30_知识库/B.md", "--root", str(vault), "--date", "2026-07-14")
        assert "query_count: 2" in page_b.read_text(encoding="utf-8")

        bad = vault / "30_知识库/Bad.md"
        bad.write_text(wiki_header('"Bad"', query_count="invalid") + "\nbad\n", encoding="utf-8")
        before_failure = snapshot(vault)
        run_fail(
            str(UPDATE),
            "30_知识库/A.md",
            "30_知识库/Bad.md",
            "--vault-root",
            str(vault),
            "--date",
            "2026-07-15",
        )
        assert snapshot(vault) == before_failure, "preflight failure must prevent every write"

        for rejected in (routine, raw, schema, maintenance):
            before_rejection = snapshot(vault)
            run_fail(str(UPDATE), str(rejected), "--vault-root", str(vault))
            assert snapshot(vault) == before_rejection

        outside = vault.parent / f"{vault.name}-outside.md"
        outside.write_text(wiki_header('"Outside"') + "\noutside\n", encoding="utf-8")
        try:
            link = vault / "30_知识库/OutsideLink.md"
            link.symlink_to(outside)
            run_fail(str(UPDATE), str(link), "--vault-root", str(vault))
        finally:
            outside.unlink(missing_ok=True)


def test_fixed_layout_requires_wiki() -> None:
    with tempfile.TemporaryDirectory() as temp:
        vault = Path(temp)
        run_fail(str(QUERY), "test", "--vault-root", str(vault))


def main() -> None:
    test_literal_search()
    test_usage_updates()
    test_fixed_layout_requires_wiki()
    print("query fixture passed")


if __name__ == "__main__":
    main()
