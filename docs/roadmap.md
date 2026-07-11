---
last_updated: 2026-07-12
update_count: 11
last_queried: ""
query_count: 0
sources:
  - "[[architecture]]"
  - "[[AGENTS]]"
topic: "Sunday Note 路线图"
keywords:
  - "路线图"
  - "安装器"
  - "QuickAdd"
  - "query"
  - "lint"
  - "回归测试"
  - "audit"
---

# 路线图

## 当前判断

SundayNoteAgent 已具备安装导出、ingest、query、lint、QuickAdd rollup、迁移工具和可选论文总结能力。当前主要问题不是能力缺口，而是已有链路存在副作用、职责重叠和缺少回归保护。

下一阶段优先修复真实使用风险并删除低价值机制，不新增默认 skill、后台任务、评分字段或检索基础设施。最小版 audit 暂不进入开发队列；先用真实问题验证其必要性和稳定工作流。

## 已确认问题

- `query_search.py` 把关键词当正则表达式交给 `rg`；`C++`、`.NET`、`[` 等词会产生误匹配或切换到不同搜索语义。
- `update_query_header.py` 不验证 Wiki 路径，并且多文件更新会在后续文件校验失败时留下部分写入。
- `lint_headers.py --entry` 会读取 vault 根目录下全部 Markdown，并可通过 scope 外文件判定 scope 内页面可达；这与显式 scope 和 `audit_reachability.py` 的结果不一致。
- `lint_headers.py` 同时承担 header、index、reachability、正文正则候选和使用次数评分，已超出机械 header 粗筛职责。
- 仓库没有自动化回归测试；当前只有语法、JSON 解析和人工 fixture 检查。

## P0：建立最小回归基线

目标：用标准运行时覆盖会修改用户文件的核心路径，为后续删减和修复提供保护。

需要改动：

- 提供单一测试入口，使用 Bash、Python 标准库和 Node 内置断言，不引入测试框架或常驻依赖。
- 安装器 fixture 覆盖新 vault、已有 vault、重复安装、真实目录冲突、可选 skill 保留和配置不覆盖。
- rollup fixture 使用最小 Obsidian API stub，覆盖周统计、月统计、缺失来源、缺失目标和 required context 中止。
- query / lint fixture 覆盖特殊字符关键词、只读行为、路径边界和显式 scope。
- 默认测试不运行 Docling 模型推理或飞书网络请求；只做 CLI、配置和轻量 fixture 检查。

验收：

- 一条命令可以在临时目录完成全部核心回归检查。
- 测试不读取父 vault 个人正文，不在仓库生成缓存或运行产物。
- 每个 P0 / P1 行为修复与对应回归用例一起提交。

## P0：把 query 收缩为字面检索和只读回答

目标：统一候选检索语义，并删除低价值使用遥测带来的写入副作用。

需要改动：

- `rg` 使用 fixed-string 搜索，不把用户词解释为正则表达式。
- 对关键词做去空、大小写归一和去重；不增加分词器、向量索引或持久缓存。
- 文件名与正文使用一致的计分语义，输出分数应能由显示的命中数解释。
- 从 canonical Wiki header 中移除 `last_queried` 和 `query_count`，保留内容维护所需的 `last_updated`、`update_count`、`sources`、`topic` 和 `keywords`。
- 删除 `update_query_header.py` 及 query skill 的自动写回步骤；删除 lint 和 query 输出中围绕 query 使用次数的规则。
- 已有页面中的旧字段可以保留但不再维护，不对父 vault 做自动批量改写。

验收：

- `C++`、`.NET`、`[`、中英文短语和普通项目名均不会产生正则误匹配。
- 有无 `rg` 时，候选集合和排序原则一致。
- query 仍只检索配置中的 Wiki 和 Routine，证据文件上限保持不变。
- 普通 query 全程只读，不再因为被查询而产生高频 header diff。
- 删除 telemetry 后不影响候选检索、证据读取和个人上下文语义触发。

## P1：把 lint 收缩为诊断与显式维护

目标：消除默认写入和重复审计，让脚本名与职责一致。

需要改动：

- 用户要求检查、分析或诊断时，只输出问题和维护计划，不写维护日志、不修改 Wiki、不创建 worker。
- 只有用户明确要求执行维护时才修改文件；维护日志只记录实际执行或 blocked 的任务。
- worker 是运行时可选优化，不作为 lint skill 的必需 API 或普通任务的所有权规则。
- `lint_headers.py` 只保留 header 必需字段、格式、重复 topic 和可由 header 直接判断的机械问题。
- 从 `lint_headers.py` 删除 `--entry`、直接 index 覆盖检查、全库图遍历、正文正则候选和依赖 `query_count` 的高使用评分。
- 完整链接、歧义、零入链和入口可达性统一交给 `audit_reachability.py`，并且只读取显式 entry、scope 和 include-file。
- 低个人增量、普通搜索可替代性和知识库有效性不属于 lint 机械检查；需要时由 ingest 判断或人工抽检。

验收：

- 诊断请求没有文件写入副作用。
- `lint_headers.py` 不读取用户未指定的目录。
- 同一 reachability fixture 只存在一个权威结果。
- `SKILL.md` 删除实现特定的 worker 参数和重复输出模板后明显缩短。

## P1：清理仓库契约漂移

目标：让 README、安装说明、目录说明和实际导出产物一一对应。

需要改动：

- README 只保留项目入口和最短安装路径；安装细节归 `install/README.md`，架构边界归 `docs/architecture.md`，目录文档只描述真实目录。
- 清理仓库 `.gitignore` 中已失效的旧目录规则。
- 核对 `community-plugins.json`：默认列表只保留核心流程必需插件，可选插件不作为默认启用项。

验收：

- 文档中的仓库路径均真实存在，或明确标记为安装后父 vault 路径。
- 安装器帮助、README 和实际产物列表一致。
- 同一事实只在职责最近的文档中完整说明，其他位置只保留链接或一句入口。

## P2：精简可选论文总结能力

目标：保留单篇论文 Raw 总结主线，移除领域绑定和可合并步骤。

需要改动：

- 将具身智能术语表移出通用 paper skill；领域术语属于父 vault 本地上下文，不作为公开工具层固定资产。
- 评估把校验与最终状态写入合并为一个 finalize 命令；只有能删除现有脚本和工作流步骤时才实施。
- 为 `--no-parse` 准备流程和 summary 校验增加轻量 fixture；完整 Docling 解析保留为人工集成检查。
- 不增加自动联网补 metadata、模型下载器、论文推荐或跨论文知识库写入。

验收：

- 可选 skill 保持领域中立，主流程命令数量不增加。
- 默认测试不要求 GPU、模型 artifacts 或网络。
- 论文产物仍只进入父 vault 的导入工作区、Raw 和 figures 目录。

## P2：压缩快照型配置

目标：减少 Claudian / Obsidian 插件版本变化带来的无关配置负担。

需要改动：

- 先验证 Claudian 可工作的最小配置字段，再删除模型选择、UI 偏好和可由插件默认值提供的快照字段。
- 保留 Codex provider 启用、workspace-write 安全模式和必要入口配置，不保存设备路径、环境变量、会话或权限运行状态。
- layout snapshot 继续独立保存，不并入安装器自动覆盖流程。

验收：

- 新 vault 能打开 Claudian 并发现导出的 skills。
- 共享配置不固定具体设备、临时模型选择或个人 UI 偏好。
- 插件升级产生的配置 diff 明显减少。

## P3：用真实抽检验证 audit 是否值得固化

目标：先验证知识库有效性抽检能否稳定改变维护决策，再决定是否新增 skill。

验证方式：

- 人工选择 3 轮真实问题，对比使用个人知识库与不使用个人知识库的回答。
- 只记录具体个人增量、错误引用、缺失上下文和由此产生的维护动作，不建设评分系统。
- 只有当输入、对照方式和输出契约连续稳定，并且结果实际改变 lint / ingest 决策时，才新增最小 `sunday-note-audit` skill。
- 如需固化，第一版只包含 `SKILL.md`，不新增脚本、不写 Wiki、不更新 header、不进入日常 query / ingest。

验收：

- 未达到稳定复用门槛时不新增 audit skill。
- Audit 与 `audit_reachability.py` 名称相近但职责明确：前者评估个人增量，后者只审计链接图。

## 持续约束

- Query 由语义自然触发，不要求用户显式调用，也不在回答中重复说明检索机制。
- 个人上下文通过正文和真实兴趣关键词表达，不使用“个人上下文”通用 keyword 标记相关笔记。
- 不新增复杂 Dream、后台自动维护、向量数据库或 Dataview 硬依赖。
- 不新增 `density_score`、`value_score` 等主观评分字段。
- 不把个人上下文拆成多个偏好页。
- 不为 subagent 建通用框架，不把特定运行时参数写成跨 agent 契约。
- 不恢复 Weekly / Monthly 专用脚本；rollup 可从最小模板创建缺失的周/月目标，具体 QuickAdd choice 和个人模板内容继续由父 vault 维护。
- 不扩展 rollup 为任意工作流 DSL；新增配置能力必须来自已出现的第二个真实复用场景。
- 机械检查交给小脚本，语义判断留给 skill 或用户；能删除旧机制时不并行增加新机制。
