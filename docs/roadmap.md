---
last_updated: 2026-07-04
update_count: 5
last_queried: ""
query_count: 0
sources:
  - "[[architecture]]"
  - "[[AGENTS]]"
topic: "Sunday Note 路线图"
keywords:
  - "路线图"
  - "lint"
  - "audit"
  - "知识库有效性"
  - "query"
  - "ingest"
  - "subagent"
---

# 路线图

## 摘要

SundayNoteAgent 的当前重点是降低知识库维护任务的上下文压力，让 skill 保持窄职责、可验证、可迁移。`ingest`、`query` 和 `lint` 已形成基础闭环；后续开发优先补齐 audit 抽检，并继续压低日常 ingest / query 的默认成本。

## P0：新增最小版 sunday-note-audit

目标：新增 `sunday-note-audit` skill，评估个人知识库是否提供普通搜索无法替代的个人增量。

需要改动：

- 新增 `skills/sunday-note-audit/SKILL.md`。
- frontmatter 只包含 `name` 和 `description`。
- 明确 audit 与 lint 的边界：lint 管维护健康度，audit 评估知识库有效性。
- 工作流只定义：
  1. 选择 1-5 个用户问题、topic 或页面。
  2. 生成 KB-enabled 回答：允许读取 Wiki / query，也可搜索。
  3. 生成 KB-blind 回答：不允许读取 Wiki，但可搜索。
  4. evaluator 比较两者的具体 claim、证据来源、用户语境匹配度、决策影响和误用个人上下文风险。
  5. 输出有效性问题和可转成 lint 的维护任务。
- 不新增脚本，不写 Wiki，不更新 header，不自动触发 lint / ingest。

验收：

- Audit 不用于日常 ingest、普通 query 或常规 lint 修复。
- Audit 输出可以被人工转成 lint 维护任务。
- Audit 不进入日常 ingest / query 默认流程。

## P1：收紧 ingest 的搜索核验触发条件

目标：避免 ingest 过度搜索，保持轻量。

需要改动：

- 将 `sunday-note-ingest/SKILL.md` 的搜索核验规则收紧为：仅当需要判断普通搜索可替代性或外部事实可靠性时搜索。
- 如果资料价值来自用户项目上下文、个人事实或已确认判断，可不搜索。

验收：

- 用户提供明显个人上下文或项目决策时，不默认搜索。
- 外部资料价值不明时，可以搜索核验是否普通互联网可替代。

## 持续约束

- 不新增复杂 Dream 自动任务。
- Query 可以自动写回实际使用 Wiki 的 `last_queried` 和 `query_count`；不自动写回正文。
- 不把 audit 放进每次 ingest。
- 不新增 `density_score`、`value_score` 等 header 字段。
- 不把个人上下文拆成多个偏好页。
- 不把 `lint_headers.py` 做成语义判断器。
- 不为 subagent 建复杂框架。
- 机械检查交给脚本，语义判断交给 skill，普通 Wiki 写入交给 subagent，主 agent 负责编排和维护日志。
