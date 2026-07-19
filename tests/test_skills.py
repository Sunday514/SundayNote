#!/usr/bin/env python3
"""Dependency-free packaging checks for the core Sunday Note skills."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_SKILLS = (
    "sunday-note-context",
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
            assert "唯一的全局 Lint plan" in body and "计划不再新增任务" in body, skill_file
            assert "所有计划内 Wiki 写入均交给 subagent" in body, skill_file
            assert "机械问题只进入最终报告" in body, skill_file
            assert "用户明确要求只读" in body and "不修改文件" in body, skill_file
            assert "`raw_unlinked` 不由 Lint 直接写入 Wiki" in body, skill_file
            assert "先判断知识增量再提炼或合并" in body, skill_file
            assert "单篇小段落删改可由主 agent" not in body, skill_file

        if skill_name == "sunday-note-context":
            assert "## 工作流" in body, skill_file
            assert body.index("## 工作流") < body.index("## 问题"), skill_file
            sections = (
                "兴趣与经验",
                "价值取舍",
                "证据与知识演化",
                "判断与协作",
                "表达偏好",
            )
            assert re.findall(r"^### (.+)$", body, re.MULTILINE) == list(sections), skill_file
            assert re.findall(r"^#### (\d+)\.", body, re.MULTILINE) == [
                str(number) for number in range(1, 11)
            ], skill_file
            assert "把 `【真实任务】` 替换" in body and "除此之外不改变题意" in body, skill_file
            assert "不合并问题" in body and "不提前展示后续问题" in body, skill_file
            assert "每轮只展示一个问题" in body and "最多两题" in body, skill_file
            assert "跳过第 3 题时同步跳过第 4 题" in body, skill_file
            assert "同时展示完整页面和完整个性化响应段" in body and "一次明确确认" in body, skill_file
            template = skill_dir / "assets/个人上下文.md"
            assert template.is_file() and "使用 `assets/个人上下文.md`" in body, skill_file
            template_body = template.read_text(encoding="utf-8")
            assert re.findall(r"^## (.+)$", template_body, re.MULTILINE) == list(sections), template
            assert "### " not in template_body, template
            assert len(re.findall(r"^> ", template_body, re.MULTILINE)) == len(sections), template

        if skill_name == "sunday-note-query":
            assert "读取根目录 `个人上下文.md`" in body, skill_file
            assert "已有准确的 Wiki、Raw 或 Routine 入口时直接读取" in body, skill_file
            assert "没有准确入口时" in body and "`scripts/query_search.py" in body, skill_file

        for relative_path in re.findall(r"`(scripts/[^`]+\.py)`", body):
            assert (skill_dir / relative_path).is_file(), f"missing referenced script: {relative_path}"

    print("skill packaging fixture passed")


if __name__ == "__main__":
    main()
