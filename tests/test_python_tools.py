#!/usr/bin/env python3
"""Lightweight, dependency-free fixtures for read-only query and lint tools."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "skills/sunday-note-query/scripts/query_search.py"
LINT = ROOT / "skills/sunday-note-lint/scripts/lint_headers.py"


def run(*args: str) -> str:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    return result.stdout


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as temp:
        vault = Path(temp)
        (vault / ".sunday-note-agent/config").mkdir(parents=True)
        (vault / "20_每日记录").mkdir()
        (vault / "30_知识库").mkdir()
        (vault / "outside").mkdir()
        (vault / ".sunday-note-agent/config/sunday-note-vault.yaml").write_text(
            """layers:
  routine:
    daily: "20_每日记录"
  wiki: "30_知识库"
""",
            encoding="utf-8",
        )
        header = """---
last_updated: 2026-07-12
update_count: 1
last_queried: ""
query_count: 0
sources: ["fixture"]
topic: "测试主题"
keywords: ["机器人"]
---
"""
        (vault / "30_知识库/机器人.md").write_text(header + "\n机器人导航。\n", encoding="utf-8")
        (vault / "20_每日记录/2026-07-12.md").write_text("今天阅读机器人论文。\n", encoding="utf-8")
        (vault / "outside/私人正文.md").write_text("机器人不应进入搜索范围。\n", encoding="utf-8")

        before = snapshot(vault)
        query_output = run(str(QUERY), "机器人", "--vault-root", str(vault))
        assert "30_知识库" in query_output
        assert "20_每日记录" in query_output
        assert "私人正文" not in query_output
        assert snapshot(vault) == before, "query must not modify the vault"

        lint_output = run(
            str(LINT),
            "--root",
            str(vault),
            "--scope",
            "30_知识库",
            "--format",
            "json",
        )
        reports = json.loads(lint_output)
        assert [report["path"].replace("\\", "/") for report in reports] == ["30_知识库/机器人.md"]
        assert snapshot(vault) == before, "lint must not modify the vault"

    print("python tool fixture passed")


if __name__ == "__main__":
    main()
