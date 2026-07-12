---
last_updated: 2026-07-12
update_count: 21
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

待办按 Lint、Query、集成导出和后续维护分组。同组子项可以协同开发，每个子项保留独立模块、验收条件和 fixture。

## 已完成

- 安装器支持重复安装和更新，托管文件覆盖更新，本地配置与个人内容保持不变。
- Daily、Weekly、month pack 最小模板和通用 rollup 已纳入仓库维护。
- `tests/run.sh` 已提供安装器、rollup、Query/Lint 基础 fixture 的统一入口。
- 架构文档、目录文档和 scaffold 已同步 Wiki 中心知识流。
- 项目开发规则允许父 vault 作为显式临时集成测试实例；自动回归和验收仍以通用 fixture 为准。
- P0-A1 Ingest skill 已固定为从指定 Raw、Routine 或已确认对话向 Wiki 沉淀知识，包含最小写作契约、来源链接和明确写入边界。

## P0-B：Lint

### P0-B1：分层来源覆盖审计

模块：`skills/sunday-note-lint/scripts/audit_reachability.py`

目标：提供只读、确定性的 Wiki 导航与来源覆盖报告。

图模型：

- Wiki 导航只计算 `Wiki → Wiki`，从 Wiki index 检查 Wiki scope 可达性。
- Raw 承接只计算 `Wiki → Raw`，每份长期 Raw 至少需要一个 Wiki backlink。
- Routine 只验证已有的 `Wiki → Routine` 链接，不检查 Routine backlink。
- Raw 和 Routine 参与链接解析，不参与 Wiki 导航可达性。
- Journal、Schema、`.import_files/` 和未显式指定的目录不进入审计。

实现内容：

- CLI 明确接收 Wiki entry、Wiki scope、Raw scope、Routine scope、vault root 和输出格式。
- 复用 wikilink、Markdown link、路径解析和歧义检测能力。
- 分别构建 Wiki 导航边、Raw backlink 和 Routine 证据链接。
- 输出 `wiki_unreachable`、`raw_unlinked`、`broken_links` 和 `ambiguous_links`。
- 输出 Markdown 和 JSON；不写文件，不维护缓存或运行状态。

验收：

- fixture 覆盖 Wiki→Wiki、Wiki→Raw、Wiki→Project、断链和同名歧义。
- Raw 建立 Wiki backlink 后从 `raw_unlinked` 消失。
- 普通 Daily 无 backlink 不进入报告。
- Wiki index 可达性只计算 Wiki scope。
- 审计不读取指定范围外的目录。

### P0-B2：Wiki header 检查

模块：`skills/sunday-note-lint/scripts/lint_headers.py`

目标：只执行可由 Wiki header 确定的机械检查。

实现内容：

- 检查必需字段、日期、非负计数、空 `sources`、空 `topic`、空 `keywords` 和重复 `topic`。
- 保留 `query_count` 与 `last_queried` 的格式和一致性检查。
- 输出 Markdown 和 JSON，并保持只读。
- CLI 只保留 scope、root、排除项、格式和结果数量等直接相关参数。
- index、入口可达性、链接图和正文正则候选由其他模块负责。

验收：

- 脚本只读取显式 scope。
- header 合法与常见错误均有标准库 fixture。
- 输出不包含正文质量、链接可达性或主观价值判断。
- 运行前后输入文件字节不变。

### P0-B3：Lint skill

模块：`skills/sunday-note-lint/SKILL.md`

依赖：P0-B1、P0-B2。

目标：诊断 Wiki 健康度，并在用户明确要求时执行 Wiki 维护。

实现内容：

- 诊断请求只读取、报告问题和给出建议。
- header 检查调用 `lint_headers.py`，链接与覆盖检查调用 `audit_reachability.py`。
- Raw / Routine 只作为来源目标读取，不进入普通改写范围。
- `raw_unlinked` 交给 Ingest 承接；Routine 无 backlink 不作为问题。
- 只有用户明确要求执行维护时才修改 Wiki。
- 维护日志只记录真实内容修改；诊断、blocked 和无变更运行不写日志。
- worker 作为运行时可选优化，不写入固定工作流或 API。
- `query_count` 只作为复查优先级的弱信号。

验收：

- skill 正文保持简洁，frontmatter 只包含 `name` 和 `description`。
- 诊断模式没有文件写入和 worker 创建。
- 两个脚本的职责没有重叠。
- 删除、归档、个人判断和证据不足的修改需要用户确认。

## P0-C：Query

### P0-C1：Wiki 字面检索

模块：`skills/sunday-note-query/scripts/query_search.py`

目标：以 Wiki 为唯一搜索范围，输出小而可解释的候选列表。

实现内容：

- 从 vault 配置解析 Wiki 路径，只扫描该范围内的 Markdown。
- 关键词去空、大小写归一、按首次出现顺序去重，并保留完整短语。
- `rg` 使用 fixed-string，只负责候选发现。
- Python 统一计算文件名和正文的字面命中数；总分能够由显示的各词命中数相加得到。
- 有无 `rg` 使用同一评分与排序原则。
- 候选输出路径、总分、各词命中、`topic`、`keywords` 和 `sources`。
- 无匹配时返回明确的 Wiki 覆盖缺口；不搜索 Raw / Routine，不增加 scope 回退。

验收：

- `C++`、`.NET`、`[`、中英文短语和普通项目名均按字面匹配。
- 重复词只计一次，文件名与正文计分一致。
- 有无 `rg` 的候选集合和排序原则一致。
- 输出不包含 Raw / Routine 文件，运行前后 vault 文件不变。

### P0-C2：Wiki 使用记录

模块：`skills/sunday-note-query/scripts/update_query_header.py`

目标：安全记录实际参与回答的 Wiki 页面使用次数。

实现内容：

- 通过 vault 配置解析 Wiki 根目录，只接受其中的 Markdown 页面。
- Raw、Routine、Journal、Schema 和 vault 外路径全部拒绝。
- 所有目标先完成路径、header、字段和计数预检，再开始写入。
- 同一页面同一轮只计一次。
- 只更新 `last_queried` 和 `query_count`；正文及其他 header 字段保持不变。
- 用户明确要求完全只读时跳过记录。

验收：

- 候选命中和精读后排除的页面不计数。
- 实际作为回答依据或来源路由的 Wiki 页面计数加一。
- 任一目标预检失败时全部目标保持不变。
- 路径边界、去重和正文不变由标准库 fixture 覆盖。

### P0-C3：Query skill

模块：`skills/sunday-note-query/SKILL.md`

依赖：P0-C1、P0-C2；发布依赖 P0-B1。

目标：用最少 Wiki 证据回答问题，并按需读取页面中的来源链接。

实现内容：

- 从用户问题提取 3–8 个名称、日期、项目线索、术语或短语。
- 调用 Wiki 字面检索并选择不超过 3 个页面精读。
- 由 agent 判断是否读取 Wiki 中直接相关的 Raw / Routine 链接，不引入递归搜索或图遍历机制。
- Wiki 已足够回答时不读取来源；需要事实细节、来源限制、项目验证或冲突核对时读取链接文档。
- 只为最终影响回答的 Wiki 页面更新使用记录。
- 新产生的稳定知识给出 Ingest 建议；Query 不修改 Wiki 正文。

验收：

- skill 正文保持简洁，frontmatter 只包含 `name` 和 `description`。
- 普通 Query 不直接搜索 Raw / Routine。
- Wiki 无匹配时报告覆盖缺口。
- 同一轮的候选、精读页面和实际证据范围能够明确区分。

## P0-D：集成、测试与导出

### P0-D1：统一回归入口

模块：`tests/`

依赖：P0-A1、P0-B1 至 P0-B3、P0-C1 至 P0-C3。

目标：用一个命令验证三个 skill 相关脚本和知识流契约。

实现内容：

- `tests/run.sh` 汇总各模块 fixture，不引入测试框架或网络依赖。
- 自动回归使用临时 vault；父 vault 只用于显式临时集成检查。
- 每个 P0 模块在对应 fixture 中独立断言自己的输入、输出和写入边界。

验收：

- `bash tests/run.sh` 一次通过全部核心检查。
- 测试不依赖父 vault 的具体内容或本地状态，也不留下长期产物。

### P0-D2：安装导出

模块：`install/`、`install/README.md`

依赖：P0-D1。

目标：把更新后的三个 skill 和脚本安全导出到 vault。

实现内容：

- 安装器继续覆盖托管 skill 和脚本，保留 vault 本地配置、模板和正文。
- 安装说明记录 Wiki-only Query、来源覆盖审计和 Ingest 承接关系。
- 安装 fixture 验证新增、更新和重复运行。

验收：

- 三个 skill 和相关脚本与仓库源码一致。
- 重复安装不会覆盖 vault 本地配置或个人内容。
- 安装器不自动整理父 vault 的 Wiki、Raw 或 Routine。

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

### P1-A2：仓库忽略规则

模块：`.gitignore`

目标：只忽略本项目真实产生的本地目录和运行状态。

实现内容：

- 核对每条规则对应的当前目录或工具。
- 删除失效路径和父 vault 专用规则。
- 安装后 vault 的忽略规则继续由 `install/scaffold/.gitignore` 维护。

验收：

- 仓库本地运行状态不会进入 Git。
- 源码、模板、fixture 和受托管配置不会被误忽略。

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

1. P0-B1、P0-B2 两个 Lint 脚本可以并行实现，随后完成 P0-B3。
2. P0-C1、P0-C2 两个 Query 脚本可以并行实现；P0-B1 可用后完成 P0-C3。
3. P0-D 统一验证并导出全部 P0 改动。
4. P1 各组按实际需要独立实施。
5. P2 只在验证达到稳定复用门槛后实施。

## 持续约束

- 每个模块只保留一套权威实现，机械检查交给小脚本，语义判断留给 skill 或用户。
- 不建设全 vault 总索引、向量数据库、图数据库、后台自动维护或持久搜索缓存。
- 不新增 `density_score`、`value_score`、`confidence_score` 等主观评分字段。
- Query 只搜索 Wiki，Raw / Routine 只通过 Wiki 链接按需读取。
- `query_count` 只作为维护优先级的弱信号。
- Journal 只有用户明确指定时才进入知识流。
- 新增配置能力需要已经出现的真实复用场景。
