#!/usr/bin/env python3
"""Dependency-free packaging checks for the core Sunday Note skills."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_SKILLS = (
    "sunday-note-ingest",
    "sunday-note-lint",
    "sunday-note-query",
)
LINT_DESCRIPTION = "仅在用户显式调用 `$sunday-note-lint` 时，对整个 Wiki 执行检查与维护。"


def parse_skill(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert lines and lines[0] == "---", f"missing frontmatter: {path}"
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise AssertionError(f"unterminated frontmatter: {path}") from exc

    frontmatter: dict[str, str] = {}
    for line in lines[1:end]:
        key, separator, value = line.partition(":")
        assert separator and key.strip(), f"invalid frontmatter line in {path}: {line}"
        key = key.strip()
        assert key not in frontmatter, f"duplicate frontmatter key in {path}: {key}"
        frontmatter[key] = value.strip()
    return frontmatter, "\n".join(lines[end + 1 :])


def main() -> None:
    for skill_name in CORE_SKILLS:
        skill_dir = ROOT / "skills" / skill_name
        skill_file = skill_dir / "SKILL.md"
        frontmatter, body = parse_skill(skill_file)
        assert set(frontmatter) == {"name", "description"}, skill_file
        assert frontmatter["name"] == skill_name, skill_file
        assert frontmatter["description"], skill_file
        assert body.strip(), skill_file

        if skill_name == "sunday-note-lint":
            assert frontmatter["description"] == LINT_DESCRIPTION, skill_file
            assert "全局 Lint plan" in body and "整轮维护共用这份计划" in body, skill_file
            assert "单篇小段落删改可由主 agent 直接完成" in body, skill_file
            assert "用户明确要求只读" in body and "不修改文件" in body, skill_file
            assert "`raw_unlinked` 不由 Lint 直接写入 Wiki" in body, skill_file
            assert "先判断知识增量再提炼或合并" in body, skill_file

        for relative_path in re.findall(r"`(scripts/[^`]+\.py)`", body):
            assert (skill_dir / relative_path).is_file(), f"missing referenced script: {relative_path}"

    print("skill packaging fixture passed")


if __name__ == "__main__":
    main()
