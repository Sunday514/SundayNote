---
last_updated: 2026-07-13
update_count: 27
last_queried: ""
query_count: 0
sources:
  - "[[architecture]]"
  - "[[AGENTS]]"
topic: "Sunday Note 路线图"
keywords:
  - "路线图"
  - "Ingest"
  - "Query"
  - "Lint"
  - "Wiki"
  - "来源链接"
  - "回归测试"
---

# 路线图

## 当前方向

SundayNoteAgent 采用以下知识流：

```text
Raw / Routine ──Ingest──> Wiki
                           │
Query ──搜索 Wiki──────────┤
                           │
                           └──按链接读取 Raw / Routine

Lint ──检查 Wiki 结构、内容和向下链接
```

Raw 保存外部资料的忠实总结，Routine 保存用户活动和项目上下文，Wiki 保存稳定知识并作为默认 Query 入口。每份长期 Raw 最终都需要 Wiki backlink；Routine 只链接实际支撑稳定知识的记录。完整读写边界由 `docs/architecture.md` 和安装后的 `AGENTS.md` 定义。

待办按项目维护和后续能力分组。同组子项可以协同开发，每个子项保留独立模块、验收条件和 fixture。

## 已完成

- 安装器支持重复安装和更新，托管文件覆盖更新，本地配置与个人内容保持不变。
- Daily、Weekly、month pack 最小模板和通用 rollup 已纳入仓库维护。
- 架构文档、目录文档和 scaffold 已同步 Wiki 中心知识流。
- 项目开发规则允许父 vault 作为显式临时集成测试实例；自动回归和验收仍以通用 fixture 为准。
- P0-A1 Ingest skill 已固定为从指定 Raw、Routine 或已确认对话向 Wiki 沉淀知识，包含最小写作契约、来源链接和明确写入边界。
- P0-B1 至 P0-B3 已完成分层来源审计、确定性 Wiki header 检查和 Lint 维护编排；审计只读取显式 scope，诊断保持只读，低风险维护按任务交给 subagent 执行。
- P0-C1 至 P0-C3 已完成 Wiki-only 字面检索、安全使用记录和最小证据 Query；候选排序使用可解释的词覆盖与 header 信号，index 不占用内容页优先级，Raw / Routine 只沿直接链接按需读取。标准 fixture、父 vault 只读 A/B 和独立证据复核均已通过。
- Vault 层目录和维护文件采用固定布局；安装器、skills、QuickAdd 和论文总结工具共享同一目录契约，`.sunday-note-agent/config/` 只保存具体功能配置。
- P1-A2 仓库忽略规则已只保留本项目的 agent 开发状态；父 vault 的运行状态和生成目录由安装后的 `.gitignore` 维护。
- P0-D1 至 P0-D2 已完成统一回归和安装导出验收；`tests/run.sh` 使用临时 vault 验证三个核心 skill、Query/Lint 脚本、QuickAdd、首次安装、托管更新和重复安装。导出副本与仓库同名源文件一致，本地配置、模板及 Raw / Routine / Wiki 内容保持不变。

## P1-A：项目维护

### P1-A1：项目入口文档

模块：`README.md`、`install/README.md`、`docs/directory-structure.md`

目标：让项目入口、安装细节和目录职责各自保持单一权威说明。

实现内容：

- README 保留项目入口、最短安装路径、更新命令、测试入口和文档链接。
- 安装细节及导出产物归 `install/README.md`。
- 真实目录和父 vault 路径归 `docs/directory-structure.md`。
- 清理失效路径、重复段落和已删除 CLI 示例。

验收：

- 文档中的仓库路径真实存在，安装后路径有明确标记。
- 安装器帮助、README 和实际导出内容一致。
- 同一事实只在职责最近的文档中完整说明。

## P1-B：Vault 集成配置

### P1-B1：默认 Obsidian 插件基线

模块：`config/obsidian/community-plugins.json`

目标：默认列表只包含知识库核心流程需要的插件。

实现内容：

- 核对每个默认插件对应的实际流程。
- 可选 UI、个人偏好和未被安装流程使用的插件不进入默认列表。
- 插件文件与运行状态继续由父 vault 本地维护。

验收：

- 新 vault 能运行模板、QuickAdd 和 agent 入口。
- 删除任一默认插件前均有对应流程验证。

### P1-B2：Claudian 共享配置

模块：`config/claudian/claudian-settings.json`

目标：保留可迁移的最小 agent 入口配置。

实现内容：

- 保留 Codex provider、workspace-write 安全模式和必要入口字段。
- 模型选择、UI 偏好、设备路径、环境变量、会话和权限运行状态由父 vault 本地维护。
- layout snapshot 保持独立，不进入安装器覆盖流程。

验收：

- 新 vault 能打开 Claudian 并发现导出的 skills。
- 共享配置不固定设备或临时模型选择。
- 插件升级产生的无关配置 diff 保持最少。

## P1-C：来源工具

### P1-C1：论文总结 skill

模块：`skills/paper-summarizer/`

目标：稳定地产生来源忠实、可被 Wiki 引用的单篇 Raw 总结。

实现内容：

- 通用 skill 保持领域中立，领域术语由父 vault 本地上下文提供。
- 评估合并校验与状态写入；只有能减少命令和代码时实施。
- 为 `--no-parse` 和 summary 校验补充轻量 fixture。
- 输出提供稳定标题或路径供 Wiki wikilink 引用。
- 产物范围保持在导入工作区、Raw 和 figures。

验收：

- 默认测试不需要 GPU、模型 artifacts 或网络。
- 主流程命令数量不增加。
- skill 不直接维护跨论文 Wiki。

## P2：回答质量 Audit 可行性

模块候选：`skills/sunday-note-audit/SKILL.md`

目标：验证回答证据质量检查能否稳定改变 Ingest 或 Lint 决策，再决定是否新增 skill。

验证内容：

- 使用三个脱敏问题样本，对比只读 Wiki 与沿链接补充 Raw / Routine 后的回答。
- 记录错误引用、缺失 Wiki 承接、断裂来源关系和对应维护建议。
- 不建设评分系统，不写 Wiki，不更新 header。

验收：

- 只有连续样本产生稳定输入、输出和实际维护价值时才新增 skill。
- 第一版只包含简短 `SKILL.md`。
- Audit 负责回答证据质量，`audit_reachability.py` 负责确定性链接图，两者职责独立。

## 实施顺序

1. P1 各组按实际需要独立实施。
2. P2 只在验证达到稳定复用门槛后实施。

## 持续约束

- 每个模块只保留一套权威实现，机械检查交给小脚本，语义判断留给 skill 或用户。
- 不建设全 vault 总索引、向量数据库、图数据库、后台自动维护或持久搜索缓存。
- 不新增 `density_score`、`value_score`、`confidence_score` 等主观评分字段。
- Query 只搜索 Wiki，Raw / Routine 只通过 Wiki 链接按需读取。
- `query_count` 只作为维护优先级的弱信号。
- Journal 只有用户明确指定时才进入知识流。
- 新增配置能力需要已经出现的真实复用场景。
