# Agent 开发规则

本目录用于维护 Sunday Note 的 agent 工具层。根目录 `../AGENTS.md` 仍然是整个 vault 的通用安全边界；本文件只补充 `SundayNoteAgent/` 内部的开发规则。

## 目标

- 维护可迁移、低复杂度、服务真实使用流程的 agent 工具层。
- 优先改进 Daily、Weekly、Monthly、Project 和 Wiki 的使用闭环。
- 避免为了单次需求堆砌规则、skill 或脚本。

## 可编辑范围

默认可以编辑：

- `skills/`
- `config/sunday-note-vault.yaml`
- `automation/`
- `布局快照/`
- `知识库框架/`
- `模板/`

如需修改 `../README.md`、`../AGENTS.md`、`../CLAUDE.md` 或 `.obsidian` 配置，先说明原因和影响范围。

默认不要编辑外层个人内容目录：

- `../10_原始材料/`
- `../20_每日记录/`
- `../21_每周记录/`
- `../22_每月记录/`
- `../23_项目复盘/`
- `../30_知识库/`
- `../40_个人写作/`

## 开发原则

- 使用脱敏示例或本地模板测试，不依赖真实个人正文。
- `模板/` 用于通用 Wiki / 框架模板，可以进入 git；`个人模板/` 用于 Daily / Weekly / Monthly 和相关 QuickAdd 脚本，默认不进入 git。
- `automation/quickadd/` 保存可复用 QuickAdd 自动化脚本；脚本通过配置读取模板路径，不保存模板正文。
- 修改 skill 时遵守 `skill-creator` 规范，保持 `SKILL.md` 简洁，frontmatter 只放 `name` 和 `description`。
- skill 安装后通过父 vault `.sunday-note-agent/config/sunday-note-vault.yaml` 解析 Raw、Routine、Wiki、Journal 和 Schema 路径；本项目维护源文件 `config/sunday-note-vault.yaml`。
- 修改脚本后运行基本语法检查。
- 修改 QuickAdd、布局或 Obsidian 配置时，说明会影响哪些日常流程。
- 不把个人数据写入 skills、规则或框架文档。
