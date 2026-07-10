---
last_updated: 2026-07-06
update_count: 7
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

本文件说明 Sunday Note 的框架架构，属于 `SundayNoteAgent/docs/`。它不是 `30_知识库/` 的正文知识页。

Sunday Note 参考 Karpathy 的 LLM Wiki 思路，但采用个人知识库版本：Wiki 是 agent 可维护的长期记忆层，Routine 是用户主导的过程记录层，Journal 是默认只读的个人表达层。

最终分层是：

```text
Raw = 证据
Routine = 例行
Wiki = 记忆
Journal = 写作
Schema = 规则
```

## 分层

- Raw 对应 `10_原始材料/`。它保存已转换成 Obsidian / LLM 可读形态的来源材料，默认不改写。
- Routine 对应 `20_每日记录/`、`21_每周记录/`、`22_每月记录/`、`23_项目复盘/`。它是用户主导的过程记录层。
- Wiki 对应 `30_知识库/`。它是 agent 可维护的长期记忆层，只保存已确认、可复用、能减少未来解释成本的内容。
- Journal 对应可选的 `40_个人写作/` 骨架。具体内容和内部结构由用户自行定义，agent 默认只读。
- Schema 对应 `AGENTS.md`、`CLAUDE.md`、`.agents/`、`.sunday-note-agent/`、`SundayNoteAgent/`、`首页.md`、`个人模板/` 和必要 `.obsidian` 配置。它是规则、配置、模板和工具控制面。
- `SundayNoteAgent/config/sunday-note-vault.yaml` 是机器可读路径映射的默认值；安装器会在父 vault 缺少配置时创建 `.sunday-note-agent/config/sunday-note-vault.yaml`，负责把 Raw、Routine、Wiki、Journal 和 Schema 术语映射到当前 vault 的实际目录名。

`.import_files/` 是隐藏导入工作目录，不属于知识分层；PDF、docx、网页导出、解析中间产物和临时日志先放这里，转换后的 Markdown 来源材料再进入 Raw。

## Routine

Routine 不等同于“工作”。它表示用户主导的周期性上下文。

- Daily：当天事实、过程记录、问题、阻塞和简短总结。
- Weekly：一周的阶段压缩、项目推进和对外表达。
- Monthly：月度方向、项目组合、知识库维护和阶段判断。
- Project：长期项目状态、风险、下一步和阶段复盘。

Daily 属于 Routine，不属于 Journal。agent 写入或改写 Routine 前需要用户确认。

## Journal

Journal 是可选个人写作层。SundayNoteAgent 只在新 vault 初始化时提供 `40_个人写作/` 空目录骨架，不定义其中应保存什么内容，也不维护其内部结构。

agent 默认只读 Journal，不主动创建、改写、润色、搬运、压缩或编译到 Wiki。只有用户明确要求时，agent 才能处理其中内容。

## 信息流

常规信息流是：

```text
导入文件
  -> .import_files
  -> 10_原始材料
  -> 20_每日记录
  -> 21_每周记录 / 22_每月记录
  -> 23_项目复盘 / 30_知识库
```

导入工作区不是必经知识层。这条链路的含义是：

- 导入工作区保存可清理的导入过程文件。
- Raw 保留长期可读来源材料。
- Routine 维护当前上下文。
- Wiki 保存长期记忆，由 agent 自动化维护。
- Journal 独立存在，只在用户明确要求时被引用。
- Schema 约束维护方式。

常规知识流也可简写为：

```text
Raw -> Routine -> Wiki
```

论文整理使用同一分工：PDF 原文、解析输出、候选图像和工作日志属于导入工作区；单篇论文总结以 `10_原始材料/<论文标题>.md` 保存，实际引用的图像进入 `assets/figures/`；跨论文技术对比、方法框架、trade-off 和选型准则进入 Wiki；服务具体项目的调研报告和方案设计进入 `23_项目复盘/`。Project 阶段结束后，如果产生可复用判断或验证经验，再回写 Wiki。

## Wiki 进入门槛

只有包含个人事实、个人偏好、项目上下文、经验模式、历史决策或已确认判断的信息，才值得进入 Wiki。

Wiki 正文不保存来源结构复述；每个段落应承载可复用事实、判断、关系、约束、经验模式或已确认结论。

追加写入 Wiki 时，优先把新信息合并到已有相关段落或新增短条目。正文只写可复用知识，不写 agent 的处理过程、写入理由、分析步骤或“基于以上 / 下面整理 / 本次补充”这类解释性铺垫。因果解释、适用条件和反例可以保留，但必须是知识本身。

不进入 Wiki 的内容：

- 网络搜索可替代的资料摘要。
- 当天流水账。
- 一次性安排。
- 未验证猜测。
- 没有个人判断的摘录。
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
- Query 根据 header 判断时效、主题匹配、检索命中和证据链；实际使用 Wiki 作为证据时，直接更新 `last_queried` 和 `query_count`，只改 header，不改正文。
- Lint 检查缺字段、日期格式、计数值、缺来源、缺 `topic`、缺 `keywords` 和 topic / keyword 冲突。

## 个人上下文

个人上下文是 Wiki 内的 canonical 页面，用于集中保存长期兴趣、近期计划、推荐偏好、当前项目和明确不感兴趣的方向。它不是新的信息层，也不是对话日志。

个人上下文只收纳稳定、已确认、能降低未来沟通成本的信息。来源可以来自 Routine、Project、用户明确确认的对话总结或已沉淀的 Wiki；不要从单次聊天、未验证推断或未经用户要求的 Journal 内容直接写入。

个人上下文只在用户明确要求，或当前任务确实依赖个人偏好、计划和项目状态时使用；不要求 agent 每次回答都推荐内容，也不固定输出推荐小节。

个人上下文页面的 `keywords` 用于记录真实兴趣词、方向词、项目词或常用问法，不用于标记页面类型；不要把“个人上下文”作为通用 keyword 加到相关计划或笔记中。

当对话或资料产生新的稳定兴趣、近期计划、偏好约束或项目状态变化时，agent 只提出写回建议。Lint 可以把个人上下文更新作为维护检查项，输出候选和修复计划；写入或更新个人上下文页面前需要用户确认，并按普通 Wiki header 更新 `last_updated` 和 `update_count`。

## Index 和 Log

`30_知识库/索引.md` 是导航入口，只放核心页面、核心工作流、项目背景和待复查页面，不重复 header 信息。

`30_知识库/知识库维护日志.md` 记录 ingest、query、lint 带来的演化，例如新增、合并、进入索引、复查和 header 字段变化。Header 是页面当前维护数据，Log 是维护历史。

## 维护原则

- Raw 可以多，Wiki 必须少。
- 导入工作区可以清理，不作为知识层维护。
- Routine 记录事实和压缩上下文。
- Wiki 保存长期稳定记忆，不重复归档 Routine。
- Journal 由用户自行维护，agent 默认只读。
- Schema 由用户主导，agent 可以建议演化。
- 根目录规则用于知识库使用，`SundayNoteAgent/AGENTS.md` 用于工具层开发。
- 新建正式文件要比更新已有文件更难。
- 同一长期主题尽量只维护一个主要 Wiki 页面。
- Skill 负责触发和执行入口；执行时先读取路径映射，不直接假设目录名；详细知识仍以 Wiki 和框架文档为准。
- `30_知识库/索引.md` 和 `30_知识库/知识库维护日志.md` 是本地 Wiki 维护文件，默认不进入 Git。

## 相关链接

- [[AGENTS]]
- [[directory-structure]]
- [[Karpathy LLM Wiki]]
- [[roadmap]]
