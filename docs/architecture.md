---
last_updated: 2026-07-16
update_count: 16
last_queried: ""
query_count: 0
sources:
  - "[[AGENTS]]"
  - "[[Karpathy LLM Wiki]]"
topic: "Sunday Note 架构"
keywords:
  - "Sunday Note"
  - "架构"
  - "Raw"
  - "Routine"
  - "Wiki"
  - "Journal"
  - "Schema"
  - "Wiki Header"
---

# 架构设计

## 摘要

本文件位于 `SundayNoteAgent/docs/`，说明 Sunday Note 的框架架构。

Sunday Note 参考 Karpathy 的 LLM Wiki 思路，但采用个人知识库版本：Raw 和 Routine 是并列的证据来源，Wiki 是 agent 从两者提炼和维护的长期知识层，Journal 是默认只读的个人表达层。

最终分层是：

```text
Raw = 证据
Routine = 例行
Wiki = 记忆
Journal = 写作
Schema = 规则
```

## 分层

- Raw 对应 `10_原始材料/`。它保存论文、书籍、课程等外部资料的长期来源总结，忠实表达原有内容，不混入后续思考，默认不改写。
- Routine 对应 `20_每日记录/`、`21_每周记录/`、`22_每月记录/`、`23_项目复盘/`。它是用户主导的过程记录层。
- Wiki 对应 `30_知识库/`。它是 agent 可维护的长期记忆层，只保存已确认、可复用、能减少未来解释成本的内容。
- Journal 对应可选的 `40_个人写作/` 骨架。具体内容和内部结构由用户自行定义，agent 默认只读。
- Schema 对应 `AGENTS.md`、`.agents/`、`.sunday-note-agent/`、`SundayNoteAgent/`、`首页.md`、`个人模板/` 和必要 `.obsidian` 配置。它是规则、配置、模板和工具控制面。
- Raw、Routine、Wiki、Journal 和 Schema 使用本文件定义的固定目录名；skills、自动化脚本和安装器遵循同一布局。
- `SundayNoteAgent/templates/` 保存 Daily、Weekly 和 month pack 的最小结构契约，不包含具体打卡项或个人正文；安装器只在父 vault 对应模板缺失时创建副本。

`.import_files/` 是隐藏导入工作目录，不属于知识分层；PDF、docx、网页导出、解析中间产物和临时日志先放这里，完成整理的长期来源总结再进入 Raw。

## Routine

Routine 表示用户主导的周期性上下文。

- Daily：当天事实、过程记录、问题、阻塞和简短总结。
- Weekly：一周的阶段压缩、项目推进和对外表达。
- Monthly：月度方向、项目组合、知识库维护和阶段判断。
- Project：长期项目状态、风险、下一步和阶段复盘。

Daily 属于 Routine，不属于 Journal。agent 写入或改写 Routine 前需要用户确认。

## Journal

Journal 是可选个人写作层。安装器在目录缺失时提供 `40_个人写作/` 空目录骨架，不定义其中应保存什么内容，也不维护其内部结构。

agent 默认只读 Journal，不主动创建、改写、润色、搬运、压缩或编译到 Wiki。只有用户明确要求时，agent 才能处理其中内容。

## 信息流

知识流是：

```text
Raw / Routine ──Ingest──> Wiki
                           │
Query ──搜索 Wiki──────────┤
                           │
                           └──按链接读取 Raw / Routine

Lint ──检查 Wiki 结构、内容和向下链接
```

Raw 和 Routine 是两类并列来源：

- Raw 回答外部资料原本表达了什么，保留来源忠实总结。
- Routine 回答用户做了什么、如何判断以及项目如何验证，保留个人活动总结。
- Ingest 读取 Raw、Routine 或已确认对话，把稳定知识提炼进 Wiki，并在相关位置保留来源链接。
- Query 默认只搜索 Wiki；读取 Wiki 后，由 agent 按问题需要决定是否读取页面链接的 Raw / Routine，不实现递归搜索或额外图状态。
- Lint 只在用户显式调用 `$sunday-note-lint` 时执行。每次调用都逐页检查整个 Wiki 的知识结构、可达性和指向 Raw / Routine 的证据关系；用户未限制写入时按唯一全局计划把 Wiki 维护交给 subagent，显式只读约束下只输出计划。机械问题只报告，Lint 不把 Raw / Routine 当作普通改写对象。
- Journal 独立存在，只在用户明确要求时被引用。
- Schema 约束以上行为。

导入文件先进入 `.import_files/`，完成整理后形成 Raw 来源总结；这条导入链与 Routine 无关。知识编译关系可简写为：

```text
[Raw, Routine] -> Wiki
```

论文整理使用同一分工：PDF 原文、解析输出、候选图像和工作日志属于导入工作区；单篇论文总结以 `10_原始材料/<论文标题>.md` 保存，实际引用的图像进入 `assets/figures/`；跨论文技术对比、知识结构、方法框架、trade-off 和选型准则进入 Wiki；服务具体项目的调研报告或方案设计进入 `23_项目复盘/`，其中可复用的判断和验证经验再由 Ingest 提炼进 Wiki。

每份长期 Raw 来源总结最终都应至少被一个相关 Wiki 页面链接。没有 Wiki backlink 的 Raw 是明确的覆盖缺口，由 Lint 持续报告并交给 Ingest 承接。Routine 不要求逐篇建立 backlink；只有实际支撑稳定知识的记录才由 Wiki 链接。

Wiki 在相关知识附近保存来源关系：正文 wikilink 表达某项判断与 Raw / Routine 的关系，header `sources` 汇总页面级来源。总 index 只组织核心 Wiki 页面。初版不要求正文链接与 `sources` 严格同步，也不建设 claim 级来源模型或图数据库。

## Wiki 进入门槛

只有能为未来回答提供知识增量的内容才值得进入 Wiki。这里的增量不限定为个人项目或对话产生的信息；相较直接使用 LLM、普通网络搜索或临时重读来源，能够提高检索效率、回答深度或提供独特结构与见解，也属于增量。

知识结构化本身可以构成增量，例如把一份或多份来源中的概念、关系、矛盾、适用条件和方法差异进一步思考并整理成稳定主题页。个人事实、个人偏好、项目上下文、经验模式、历史决策和已确认判断同样属于重要增量。

Wiki 正文不保存来源结构复述；每个段落应承载可复用事实、判断、关系、约束、经验模式或已确认结论。

追加写入 Wiki 时，优先把新信息合并到已有相关段落或新增短条目。正文只写可复用知识，不写 agent 的处理过程、写入理由、分析步骤或“基于以上 / 下面整理 / 本次补充”这类解释性铺垫。因果解释、适用条件和反例可以保留，但必须是知识本身。

不进入 Wiki 的内容：

- 单篇论文、书籍或课程的来源忠实总结；这些内容保留在 Raw。
- 相较直接 LLM 回答、普通网络搜索或现有来源没有提高检索效率、回答深度或独特见解的重复内容。
- 当天流水账。
- 一次性安排。
- 未验证猜测。
- 未经结构化或提炼的摘录。
- 完整命令输出或原始日志。
- PDF、docx、解析中间产物和导入过程日志。
- 未经用户明确要求的 Journal 内容。

## Wiki Header

Wiki 页面使用短 YAML header 作为维护依据，不承载正文内容：

```yaml
last_updated: YYYY-MM-DD # 内容或来源实质变化日期
update_count: 1 # 内容或来源实质变化次数
last_queried: "" # 最近一次作为 query 证据使用的日期
query_count: 0 # 作为 query 证据使用的次数
sources: [] # 长期可追溯来源，如书籍、课程、论文、网页
topic: "" # 单一稳定主题，用于判断页面归属和合并边界
keywords: [] # 检索提示词，用于 query 候选匹配
```

Header 用于三个动作：

- Ingest 根据 header 判断是否已有同主题页面，并维护 `last_updated`、`update_count`、`sources`、`topic` 和 `keywords`。
- Query 只搜索 Wiki，根据 header 判断时效、主题匹配、检索命中和证据链；实际使用 Wiki 作为回答依据或来源路由时，更新 `last_queried` 和 `query_count`，只改 header，不改正文。
- Lint 检查缺字段、日期格式、计数值、缺来源、缺 `topic`、缺 `keywords` 和 topic / keyword 冲突。

## 个人上下文

个人上下文是 Wiki 内的 canonical 页面，集中保存长期兴趣、近期计划、推荐偏好、当前项目和明确不感兴趣的方向，只收纳经过确认的稳定信息。

个人上下文只收纳稳定、已确认、能降低未来沟通成本的信息。来源可以来自 Routine、Project、用户明确确认的对话总结或已沉淀的 Wiki；不要从单次聊天、未验证推断或未经用户要求的 Journal 内容直接写入。

个人上下文只在用户明确要求，或当前任务确实依赖个人偏好、计划和项目状态时使用；不要求 agent 每次回答都推荐内容，也不固定输出推荐小节。

个人上下文页面的 `keywords` 用于记录真实兴趣词、方向词、项目词或常用问法，不用于标记页面类型；不要把“个人上下文”作为通用 keyword 加到相关计划或笔记中。

当对话或资料产生新的稳定兴趣、近期计划、偏好约束或项目状态变化时，agent 只提出写回建议。Lint 可以把个人上下文更新作为维护检查项，输出候选和修复计划；写入或更新个人上下文页面前需要用户确认，并按普通 Wiki header 更新 `last_updated` 和 `update_count`。

## Index 和 Log

`30_知识库/索引.md` 是 Wiki 导航入口，只组织核心 Wiki 页面、核心工作流、项目背景和待复查页面，不枚举全部 Raw / Routine，也不重复 header 信息。Raw / Routine 通过相关 Wiki 页面正文中的链接按需可达。

`30_知识库/知识库维护日志.md` 记录两类事件：Ingest 新建 Wiki 页面时写一条创建登记；有实际知识维护的 Lint 在整轮结束时由主 agent 写一条整轮维护记录，汇总实际完成项、必要的计划差异和最终验证结论。普通 Ingest 页面更新、Query、只读或无实际知识维护的 Lint、blocked 任务、未执行建议以及仅更新 `last_queried` / `query_count` 不写维护日志。Header 是页面当前维护状态，Log 是页面创建与整轮维护历史。

## 维护原则

- Raw 可以多，Wiki 必须少；每份长期 Raw 最终都应由相关 Wiki 页面链接。
- 导入工作区可以清理，不作为知识层维护。
- Raw 和 Routine 是并列来源；Routine 记录事实和压缩上下文，不要求全部进入 Wiki。
- Wiki 保存能提升未来检索效率、回答深度或独特性的长期知识，不重复归档 Raw / Routine。
- Journal 由用户自行维护，agent 默认只读。
- Schema 由用户主导，agent 可以建议演化。
- 根目录规则用于知识库使用，`SundayNoteAgent/AGENTS.md` 用于工具层开发。
- 新建正式文件要比更新已有文件更难。
- 同一长期主题尽量只维护一个主要 Wiki 页面。
- Skill 负责触发和执行入口，按固定 vault 布局工作；详细知识仍以 Wiki 和框架文档为准。
- `30_知识库/索引.md` 和 `30_知识库/知识库维护日志.md` 是本地 Wiki 维护文件，默认不进入 Git。

## 相关链接

- [[AGENTS]]
- [[directory-structure]]
- [[Karpathy LLM Wiki]]
- [[roadmap]]
