---
last_updated: 2026-05-24
update_count: 1
last_queried: ""
query_count: 0
sources:
  - "[[architecture]]"
  - "[[AGENTS]]"
topic: "Sunday Note 路线图"
keywords:
  - "路线图"
  - "micro-skill"
  - "ingest"
  - "query"
  - "lint"
  - "Wiki 索引"
  - "Project Hub"
---

# 路线图

## 摘要

Sunday Note 的目标是持续降低 agent 理解用户、项目和判断方式的成本。路线图优先强化个人知识库与 SundayNoteAgent 工具层的边界，让 ingest、query、lint 三个 micro-skill 围绕个人增量、低熵维护和可追溯链接工作。

## P1：强化三个 micro-skill

目标：让 skill 的输出直接支持个人增量判断和低上下文成本。

### sunday-note-ingest

- 增加输出字段：个人增量、搜索可替代性、Agent 使用价值。
- 保留来源、摘要、事实、推断、待确认问题、Wiki 入库判断、canonical 页面建议。
- 输出链接、索引和维护日志更新建议，但不直接写入 Wiki。

### sunday-note-query

- 明确读取顺序：根 `AGENTS.md`、路径映射 yaml、Wiki index、canonical Wiki、Project、必要 Routine、必要 Raw。
- 输出区分：个人知识库依据、通用推理、待确认内容、是否建议写回。
- 写回建议只在回答产生稳定个人判断时提出。
- 明确 `query_search.py` 的位置和用途，避免相对路径歧义。

### sunday-note-lint

- 增加降熵检查项：通用内容、缺少个人增量、低 Agent 使用价值、上下文拖累、过度摄取。
- 保留重复主题、未索引页面、缺 sources/last_updated/update_count/last_queried/query_count/topic/keywords、弱链接和边界混淆检查。
- 只输出修复计划和维护日志建议，不默认改写页面。

验证：

- 每个 skill 的 `SKILL.md` frontmatter 只包含 `name` 和 `description`。
- 三个 skill 仍保持窄触发，不合并、不自动链式调用。

## P1：补强 Wiki 索引

目标：让 `30_知识库/索引.md` 成为 agent query 的高价值导航入口。

- 只放核心方法、核心工作流、核心概念、核心经验、长期项目背景和待复查页面。
- 不把索引做成全量目录。
- 将重要 canonical Wiki 页面按查询价值加入索引。
- 将缺个人判断、长期未 query 或需要降熵的页面列入待复查。

验证：

- query 可以先读索引，再定位少量 canonical 页面。
- 未进入索引的页面默认不被视为核心长期知识。

## P1：建立 Project Hub

目标：让项目状态查询优先读取 Project 页面，而不是翻 Daily。

- 为长期项目建立少量 Project 页面，例如 Sunday Note 和 SundayNoteAgent。
- 每个 Project 页面维护目标、当前状态、最近进展、风险、下一步、相关 Weekly / Monthly / Wiki 链接。
- Project 页面作为 Routine 中的项目上下文 hub，不替代 Wiki 的长期判断。

验证：

- 用户问项目状态时，agent 能先读 Project 页面。
- Project 页面能回链到近期 Routine 和相关 canonical Wiki。

## P2：规范维护日志

目标：让维护日志记录知识库演化，而不是普通聊天流水。

- 每条维护记录包含：操作、范围、变更、进入索引的页面、待复查项。
- 记录 ingest、query、lint、schema 带来的长期知识库变化。
- 不记录一次性聊天、临时命令输出或个人正文。

验证：

- lint 输出能直接生成维护日志建议。
- query 能通过维护日志理解最近的知识库演化。

## P3：暂缓通用模板

目标：避免模板反向规定内容结构。

- `templates/` 仅保留占位。
- 父 vault 的 `个人模板/` 继续保存本地实际模板正文。
- 不维护通用 Wiki、论文、书籍或课程模板。
- Ingest 根据材料自身逻辑设计结构，按 SCQA 和金字塔原则组织写作。
- 只有当真实使用中出现稳定、重复、可迁移的结构，再评估新增通用模板。

验证：

- 工具层不保存个人模板正文。
- Ingest 不依赖固定模板也能生成清晰的写入计划。

## 持续检查

- 根目录规则只约束个人知识库，不放具体 skill 输出格式或插件细节。
- `SundayNoteAgent/AGENTS.md` 只约束工具开发，不写入个人数据。
- skills 默认不触发，一个请求默认最多触发一个 skill。
- Obsidian 链接遵守 `index -> canonical Wiki -> sources / Project / Routine`。
- Wiki 只保存能提升 agent 判断能力的个人增量。
