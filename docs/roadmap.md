---
status: draft
updated: 2026-05-23
sources:
  - "[[architecture]]"
  - "[[AGENTS]]"
---

# 路线图

## Summary

Sunday Note 的目标是持续降低 agent 理解用户、项目和判断方式的成本。路线图优先强化个人知识库与 SundayNoteAgent 工具层的边界，让 ingest、query、lint 三个 micro-skill 围绕个人增量、低熵维护和可追溯链接工作。

## P0：根规则补齐个人增量原则

目标：让根目录 `AGENTS.md` 明确知识库的最高取舍标准。

- 将核心动机表述为：让 agent 更懂用户，不是保存更多资料。
- 明确个人增量原则：进入长期知识库的信息，必须相比网络搜索结果有个人事实、个人判断、项目上下文、经验模式或长期决策价值。
- 明确 Wiki 不接收网络搜索可替代的普通摘要、未经确认的 AI 总结、没有个人判断的摘录、当天流水账和临时命令输出。
- 保持根 `AGENTS.md` 简短，只保留方向、分层、写入边界、skill 路由和链接原则。

验证：

- 根 `AGENTS.md` 能在 1-2 分钟内读完。
- agent 在写入 Wiki 前能明确说明个人增量和写入理由。

## P1：强化三个 micro-skill

目标：让 skill 的输出直接支持个人增量判断和低上下文成本。

### sunday-note-ingest

- 增加输出字段：`Personal delta`、`Search substitutability`、`Agent-use value`。
- 保留 source、summary、facts、inferences、open questions、Wiki-entry judgment、suggested canonical page。
- 输出链接、索引和维护日志更新建议，但不直接写入 Wiki。

### sunday-note-query

- 明确读取顺序：根 `AGENTS.md`、路径映射 yaml、Wiki index、canonical Wiki、Project、必要 Routine、必要 Raw。
- 输出区分：个人知识库依据、通用推理、待确认内容、是否建议写回。
- 写回建议只在回答产生稳定个人判断时提出。
- 明确 `query_search.py` 的位置和用途，避免相对路径歧义。

### sunday-note-lint

- 增加降熵检查项：`Generic content`、`No personal delta`、`Low agent-use value`、`Context drag`、`Over-ingested`。
- 保留重复主题、未索引页面、stale 页面、缺 sources/status/updated、弱链接和边界混淆检查。
- 只输出修复计划和维护日志建议，不默认改写页面。

验证：

- 每个 skill 的 `SKILL.md` frontmatter 只包含 `name` 和 `description`。
- 三个 skill 仍保持窄触发，不合并、不自动链式调用。

## P1：补强 Wiki 索引

目标：让 `30_知识库/索引.md` 成为 agent query 的高价值导航入口。

- 只放核心方法、核心工作流、核心概念、核心经验、长期项目背景和待复查页面。
- 不把索引做成全量目录。
- 将重要 canonical Wiki 页面按查询价值加入索引。
- 将 draft、缺个人判断或需要降熵的页面列入待复查。

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

## P2：更新 Wiki 模板

目标：让每个 canonical Wiki 页面说明未来 agent 何时应该使用它。

- 在通用 Wiki 模板中增加 `Agent 使用场景` 小节。
- 建议字段包括：未来 agent 应在什么问题中读取本页、本页能改变哪些判断、不适用场景。
- 保留 sources、相关条目和参考来源，保证结论可追溯。

验证：

- 新建 Wiki 页面能自然说明 agent-use value。
- 模板仍保持通用，不绑定单个知识库 case。

## P2：规范维护日志

目标：让维护日志记录知识库演化，而不是普通聊天流水。

- 每条维护记录包含：操作、范围、变更、进入索引的页面、待复查项。
- 记录 ingest、query、lint、schema 带来的长期知识库变化。
- 不记录一次性聊天、临时命令输出或个人正文。

验证：

- lint 输出能直接生成维护日志建议。
- query 能通过维护日志理解最近的知识库演化。

## P2：处理飞书导出脚本归属

目标：确认 `scripts/export_feishu_docx.py` 是否属于可复用工具层能力。

- 如果纳入工具层，补充脚本说明、输入输出边界和基本验证方式。
- 如果只是一次性迁移工具，不写入长期工具契约。
- 脚本不得硬编码父 vault 的个人目录或本机绝对路径。

验证：

- `git status` 中不保留无意图的未跟踪工具脚本。
- 可复用脚本能通过配置读取路径。

## P3：暂缓模板基线目录

目标：避免在模板流程尚未稳定前增加目录复杂度。

- 继续使用 `templates/` 保存可复用通用模板。
- 父 vault 的 `个人模板/` 继续保存本地实际模板正文。
- 只有当 QuickAdd 自动化稳定且需要发布通用模板时，再评估新增模板基线目录。

验证：

- 工具层不保存个人模板正文。
- 通用模板仍可独立迁移和测试。

## 持续检查

- 根目录规则只约束个人知识库，不放具体 skill 输出格式或插件细节。
- `SundayNoteAgent/AGENTS.md` 只约束工具开发，不写入个人数据。
- skills 默认不触发，一个请求默认最多触发一个 skill。
- Obsidian 链接遵守 `Index -> Canonical Wiki -> Sources / Projects / Routine`。
- Wiki 只保存能提升 agent 判断能力的个人增量。
