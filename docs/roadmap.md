---
last_updated: 2026-07-03
update_count: 2
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
  - "编排器"
  - "知识库有效性"
  - "subagent"
  - "Wiki 维护"
---

# 路线图

## 摘要

SundayNoteAgent 的当前重点是降低知识库维护任务的上下文压力，让 skill 保持窄职责、可验证、可迁移。`ingest`、`query` 和 `lint` 已形成基础闭环；后续开发优先改进维护编排和知识库有效性评估，不扩大日常 ingest / query 的默认流程。

## P0：将 lint 调整为维护编排器

目标：`sunday-note-lint` 默认只做诊断、分解和维护计划，不承担多文件长上下文读写任务。

- Lint 读取用户指定范围和必要索引，不默认扫描全库，不默认改写 Wiki。
- Lint 输出维护任务列表，而不是一次性完成所有修复。
- 每个维护任务包含：`task_id`、目标、涉及文件、需要读取的证据、建议动作、风险、验证方式、是否适合分派 subagent。
- 用户确认具体任务后，再由窄范围执行任务读取和修改文件。
- 长文件、多文件合并、索引重组、结构性空话清理、个人上下文整理等任务优先拆分给独立 subagent；每个 subagent 只处理一个明确任务，不自行扩大范围。
- `lint_headers.py` 继续作为机械粗筛工具，只提供 header、index、重复 topic、body pattern 和维护优先级候选。
- `lint_headers.py --body-scan` 可增加过程性写入包装候选，例如“本次补充 / 基于以上 / 下面整理 / 我将更新”，保持低权重候选，不做语义裁决。

验收：

- `sunday-note-lint/SKILL.md` 明确 lint 是维护计划编排器。
- Lint 输出格式能直接转成单个维护任务。
- 对同一范围执行 lint 时，用户能选择只执行某个任务，而不是被迫接受整批修改。
- 脚本仍不自动改写 Wiki。

## P0：新增 sunday-note-audit

目标：新增 `sunday-note-audit` skill，用于抽样评估个人知识库和工具链是否提供普通搜索无法替代的个人增量。

- Audit 不用于日常 ingest、普通 query 或常规 lint 修复。
- Audit 用于开发优化、知识库质量抽查、怀疑 Wiki 低增量、评估 query / ingest / lint 是否有效时。
- Audit 可抽样 3-5 个 Wiki 页面、topic 或真实问题。
- 对每个问题生成两个独立回答：一个允许读取 Wiki / query 并可搜索，另一个不允许读取 Wiki 但可搜索。
- 第三个 evaluator 比较两者回答，只看具体 claim、证据来源、用户语境匹配度、决策影响和误用个人上下文风险。
- Audit 输出高增量页面、低增量页面、query 检索失败、ingest 写入质量问题、lint 可新增检查模式和建议维护任务。
- Audit 默认只评估和建议，不修改 Wiki，不更新 header，不写维护日志。

验收：

- 新增 `skills/sunday-note-audit/SKILL.md`，frontmatter 只包含 `name` 和 `description`。
- Skill 描述能与 `sunday-note-lint` 区分：lint 管维护健康度，audit 评估知识库有效性。
- Audit 工作流明确三方对照：KB-enabled、KB-blind、evaluator。
- Audit 输出能转成 lint 维护任务，但不自动触发 lint 或 ingest。

## P1：保持维护日志为建议项

目标：维护日志记录知识库演化，但不成为自动写入负担。

- Ingest、query、lint 和 audit 只有在涉及长期结构变化时才建议维护日志。
- 建议记录操作、范围、变更、进入索引的页面、待复查项。
- 不记录一次性聊天、临时命令输出、个人正文或 agent 运行流水。

验收：

- Skill 只输出维护日志建议，不默认写入维护日志。
- 维护日志建议能说明为什么这次变化值得长期记录。

## 持续约束

- 不新增复杂 Dream 自动任务。
- 不让 lint 自动改写 Wiki。
- 不让 query 自动写回 header 或正文。
- 不把知识库有效性抽检放入每次 ingest 默认流程。
- 不新增 `density_score`、`value_score` 等 header 字段。
- 不把个人上下文拆成多个偏好页。
- 不把 `lint_headers.py` 做成语义判断器。
- 机械检查交给脚本，语义判断交给 skill，写入交给用户确认。
