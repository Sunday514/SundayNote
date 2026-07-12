---
last_updated: 2026-07-12
update_count: 16
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

## 当前判断

SundayNoteAgent 已具备安装导出、Ingest、Query、Lint、QuickAdd rollup、迁移工具和可选论文总结能力。下一阶段不增加新的知识层、搜索基础设施或后台维护机制，重点是把现有能力收缩到清晰的 LLM Wiki 知识流：

```text
Raw / Routine ──Ingest──> Wiki
                           │
Query ──搜索 Wiki──────────┤
                           │
                           └──按链接读取 Raw / Routine

Lint ──检查 Wiki 结构、内容和向下链接
```

三个核心 skill 以 Wiki 为维护目标和默认查询入口，Raw / Routine 提供来源证据：

- Raw 保存论文、书籍、课程等来源的忠实总结，不混入后续思考、跨来源判断或项目结论。
- Routine 保存用户主导的过程上下文；Project 是其中承载目标、约束、决策和验证的视图。
- Wiki 保存从 Raw、Routine 和已确认对话中提炼出的稳定知识，是默认查询入口和 agent 主要维护目标。
- Journal 保持用户个人表达层，除非用户明确指定，否则不进入 Ingest、Query 或 Lint。
- `.import_files/` 继续作为导入工作区，不进入知识图和普通查询。

Wiki 在每个主题页面的相应判断、方法、限制或项目应用旁保留来源链接。`30_知识库/索引.md` 只组织核心 Wiki 页面；Raw / Routine 通过主题 Wiki 页面按需可达。

## 目标契约

### 可达性

- 每份长期 Raw 来源总结最终都应至少被一个相关 Wiki 页面链接。
- Raw 中没有 Wiki backlink 的文档属于明确的 Wiki 覆盖缺口；Lint 持续生成未链接 Raw 清单，Ingest 负责建立承接关系。
- Routine 不要求逐篇进入 Wiki。只有支撑稳定判断、项目决策或个人长期上下文的记录才建立链接。
- Wiki 可以通过 Project、Weekly 或 Monthly 间接到达 Daily，不为追求覆盖率把每篇 Daily 直接加入 Wiki。
- 来源链接优先放在正文中对应结论附近；Wiki header 的 `sources` 只保留页面级来源集合。初版不检查两者严格同步，也不建设 claim 级来源模型。
- 不在 Raw / Routine 中维护反向链接；Obsidian backlink 和 Wiki 的正向链接提供反向发现能力。

### 读写边界

| 层 | Ingest | Query | Lint |
|---|---|---|---|
| Raw | 读取来源总结 | 只沿 Wiki 链接按需读取 | 只验证链接和未编译候选 |
| Routine | 读取稳定事实、项目决策和验证 | 只沿 Wiki 链接按需读取 | 只验证 Wiki 指向的目标 |
| Wiki | 创建或更新稳定知识 | 默认搜索、读取；只更新使用记录 | 诊断；获得明确授权后维护 |
| Journal | 用户明确指定时读取 | 用户明确指定时读取 | 不默认检查 |
| Schema | 读取规则与路径配置 | 仅工作流问题需要 | 由仓库开发流程维护 |

三个 skill 以 Wiki 为维护目标和默认检索入口，并按任务需要读取 Raw / Routine 证据。

### Query 使用记录

- `query_count` 表示 Wiki 页面实际作为最终回答依据或来源路由的次数；搜索候选不计数。
- `last_queried` 表示最近一次实际使用日期。
- 只统计最终影响回答的 Wiki 页面；仅被命中、精读后排除或重复读取的页面不计数。
- 同一页面同一轮最多计一次；Raw / Routine 不增加 Query header。
- 查询只允许更新这两个 Wiki header 字段，不因查询修改正文、`last_updated`、`update_count`、index 或维护日志。
- 使用次数只是维护优先级的弱信号，不能单独决定合并、归档或删除。

## 已完成：同步知识流契约

目标：在修改 skill 和脚本前，先让仓库规则对 Raw、Routine、Wiki 和来源链接使用同一套定义。

已同步：

- 重写 `docs/architecture.md` 中的信息流、Wiki 进入门槛、来源关系和三个核心操作。
- 在 `docs/directory-structure.md` 中明确 `10_原始材料/` 是长期来源总结层，`.import_files/` 才是导入和中间产物工作区。
- 更新 `install/scaffold/AGENTS.md`，使安装后的 agent 只把 Wiki 作为知识维护目标；Raw / Routine 默认不由普通知识维护改写。
- 保留现有目录和 `sunday-note-vault.yaml` 路径键，不重命名 `10_原始材料/`，不迁移父 vault 文件。
- 明确 Wiki 正文链接和 header `sources` 的分工；不新增来源关系数据库、页面类型系统或图索引缓存。
- 文档统一描述 Query 的 Wiki-only 搜索、Lint 的 Wiki 诊断范围和维护日志的真实内容变更记录。

验收：

- README 只提供入口，架构文档说明知识流，目录文档说明真实目录，scaffold 提供可执行规则。
- 同一层的读取权限、写入权限和链接职责在所有文档中一致。
- 文档不会把“从 Wiki 可达”描述成“总 index 必须枚举所有 Raw / Routine”。
- 长期 Raw 必须有 Wiki backlink；Routine 仍只链接实际支撑稳定知识的记录。
- 不新增目录、manifest、数据库、评分字段或后台任务。

## P0：建立 Wiki 来源覆盖基线

目标：先确认长期 Raw 来源总结都已由 Wiki 承接，再启用 Wiki-only Query，避免形成知识盲区。

需要改动：

- 使用脱敏 fixture 定义三类关系：Wiki 到 Raw、Wiki 到 Project / Routine、Wiki 到 Wiki。
- 对父 vault 做一次只读覆盖审计，统计：
  - 有 Wiki backlink 的 Raw 来源总结；
  - 没有 Wiki backlink 的 Raw 来源总结；
  - Wiki 中无法解析的 Raw / Routine 链接；
  - 能从核心 Wiki index 到达的 Wiki 页面。
- Lint 每次覆盖检查都输出“未链接 Raw 清单”；初版只生成确定性报告，不新增持久状态文件，也不让清单本身产生 Wiki backlink。
- 不自动批量创建 Wiki、不自动把所有来源塞入 index；优先把未链接 Raw 补入已有同主题 Wiki，只有缺少稳定主题页时才新建。
- 先完成必要的 Wiki 承接，再切换 Query 搜索范围。

验收：

- VLA 强化学习一类已有主题能先命中 Wiki 页面，再从正文链接到对应论文总结或项目记录。
- 每份未被 Wiki 承接的长期 Raw 总结都进入未链接 Raw 清单，并持续保留到相关 Wiki backlink 建立。
- 普通 Daily 没有 Wiki backlink 不构成问题。
- 覆盖审计只读，不修改父 vault。

## P0：把 Ingest 收缩为 Raw / Routine 到 Wiki 的编译入口

目标：Ingest 判断来源中哪些稳定增量值得进入 Wiki，并维护对应来源链接。

需要改动：

- 精简 `skills/sunday-note-ingest/SKILL.md`：
  - 输入是用户指定的 Raw 总结、Routine / Project 记录或已确认对话信息；
  - 默认写入目标只有 Wiki；
  - 优先更新已有同主题页面，新建页面门槛高于更新；
  - 不改写 Raw 来源总结，不自动整理 Routine，不摄取 Journal；
  - 只有用户明确要求处理 Journal 时才将其中已确认、可复用内容作为来源。
- 保留现有知识增量判断，并明确检索效率、回答深度、独特见解和知识结构化都可以构成增量，不要求增量必须来自个人项目或对话。
- 把来源事实、跨来源综合、项目结论和用户确认信息分开表达，禁止把 agent 推断写成来源结论。
- 在 Wiki 的具体判断附近加入 Raw / Routine wikilink；`sources` 汇总页面级来源。
- 新来源只影响局部主题时不更新总 index；只有新增核心 Wiki 入口或导航关系变化时才维护 index。
- 维护日志只记录实际执行的新增、合并或重要修订，不记录纯分析和未执行建议。
- 外部 PDF、书籍或课程的来源总结仍由 paper summarizer、迁移工具或用户准备；不把通用来源解析重新塞进 Ingest skill。

需要删除或收缩：

- “为材料选择 Raw / Routine / Wiki / Journal / Schema 任意去向”的宽泛路由职责。
- 固定 SCQA、金字塔等写作框架提示；保留“结论、证据、适用条件和来源链接”这一最小内容契约。
- 与 Lint 重复的全库价值评估、孤立页检查和维护编排。

验收：

- 给定一篇论文总结，Ingest 更新相关 Wiki 判断并在对应位置链接该总结，Raw 文件不变。
- 给定一个项目验证结论，Ingest 只把稳定、可复用部分写入 Wiki，并链接原 Project 记录。
- 同一主题重复摄取时优先合并，不产生按来源堆积的 Wiki 页面。
- Ingest 不会为了建立可达性而链接所有 Routine 文件。

## P0：把 Query 收缩为 Wiki 搜索和按链接读取证据

目标：Wiki 成为唯一默认搜索入口；Raw / Routine 只通过已选 Wiki 页面中的链接按需读取。

需要改动：

- 修改 `query_search.py`，只读取配置中的 Wiki 路径。
- `rg` 使用 fixed-string；关键词去空、大小写归一、按首次出现顺序去重，并保留中英文短语。
- `rg` 只负责快速发现候选，最终由同一个 Python 字面计分函数计算文件名和正文命中，保证有无 `rg` 时排序原则一致。
- 候选输出继续保持小而可解释：路径、总分、各关键词命中、`topic`、`keywords` 和 `sources`；不增加 embedding、摘要缓存或搜索权重配置。
- LLM 先选不超过 3 个 Wiki 页面精读，再自行判断是否读取其中与问题直接相关的 Raw / Routine 链接。该行为只在 skill 中说明一句，不实现递归搜索、固定跳数、自动图遍历或额外状态。
- Wiki 已足够回答时不读取来源；需要精确事实、方法细节、来源限制、项目验证或冲突核对时才沿链接读取。
- 普通 Query 没有 Wiki 命中时，明确报告 Wiki 覆盖缺口并建议 Ingest，不静默回退为全库 Raw / Routine 搜索。
- Query 不增加 Raw / Routine 搜索回退、扩展 scope 或其他绕过 Wiki 的兼容分支。

使用记录：

- 保留并加固 `update_query_header.py`，不删除 `last_queried` 和 `query_count`。
- 脚本通过 vault 配置验证所有目标都位于 Wiki；拒绝 Raw、Routine、Journal、Schema 和 vault 外路径。
- 所有目标先完成路径、header、字段和计数预检，再开始写入，避免后续文件失败造成可预见的部分更新。
- 只更新最终实际影响回答的 Wiki 页面；同一页面一轮去重。
- 用户明确要求本轮完全不写文件时跳过使用记录。

验收：

- `C++`、`.NET`、`[`、中英文短语和普通项目名都按字面匹配。
- Query 搜索结果不直接出现 Raw / Routine 文件。
- 读取 `VLA 强化学习` Wiki 后，从相应结论附近的链接读取所需论文总结。
- Wiki 无覆盖时返回清晰缺口，不假装 vault 中没有相关来源。
- 只有实际作为答案依据或来源路由的 Wiki 页面增加一次计数；正文和其他 header 字段字节不变。
- 多文件记录中任一目标预检失败时全部不写入。

## P0：把 Lint 收缩为 Wiki 诊断和链接审计

目标：Lint 诊断 Wiki 的结构、内容和向下链接，并把 Raw / Routine 作为只读来源目标进行验证。

Skill 需要改动：

- 精简 `skills/sunday-note-lint/SKILL.md`，删除默认写维护日志、强制创建 worker、固定任务表和运行时特定参数。
- 用户要求检查、分析或诊断时只输出问题和建议，不修改文件。
- 只有用户明确要求执行维护时才更新 Wiki；高风险、证据不足、删除、归档和个人判断继续要求确认。
- 维护日志只记录真实执行的内容修改；blocked 任务、无变更扫描和未执行建议不写日志。
- Query 使用次数只用于安排复查优先级；零使用不能证明低价值，高使用不能证明内容正确。

脚本需要改动：

- `lint_headers.py` 只保留 Wiki header 必需字段、日期和计数格式、空来源、空 topic / keywords、重复 topic，以及能由 header 直接判断的机械问题。
- 从 `lint_headers.py` 删除 `--entry`、index 覆盖、全库图遍历、正文正则候选和与 `audit_reachability.py` 重复的逻辑。
- `audit_reachability.py` 成为唯一链接图检查入口，并明确区分：
  - 需要从 Wiki index 可达的 Wiki scope；
  - 仅用于解析和验证的 Raw / Routine 文件；
  - Raw 中没有 Wiki backlink 的明确覆盖缺口。
- 链接审计只读取显式 Wiki、Raw 和 Routine 路径，不扫描 Journal、Schema 或 vault 其他目录。
- 机械脚本只报告断链、歧义、Wiki 可达性和未链接 Raw 清单；初版不判断链接位置、来源覆盖比例或 claim 级支撑关系。

验收：

- 诊断请求没有写入副作用，也不创建 worker。
- Wiki 到 Raw / Routine 的有效链接能被解析，断链能定位到源 Wiki 页面和具体目标。
- 每份 Raw 无 backlink 都进入未链接 Raw 清单；Routine 无 backlink 不进入全局问题列表。
- 同一 reachability fixture 只有 `audit_reachability.py` 一个权威结果。
- `lint_headers.py` 不读取用户未指定的目录，代码和 CLI 参数明显减少。

## P0：扩展回归基线并完成切换

目标：用一条命令保护新的 Wiki 中心知识流，然后再把它安装到父 vault。

需要补充的 fixture：

- Ingest 规则 fixture 或最小文档场景：同主题合并、正文相应位置保留来源链接、Raw / Routine 不变。
- Query：Wiki-only scope、特殊字符、完整短语、重复词、有无 `rg` 排序一致、无覆盖报告。
- Query 记录：实际证据计数、候选不计数、同轮去重、Wiki 路径边界、多目标预检和正文不变。
- Lint：Wiki index 可达性、Wiki 到 Raw / Routine 链接、断链、未链接 Raw 清单、Routine 不要求全覆盖。
- 安装器：更新后的三个 skill 和脚本能够覆盖到父 vault，父 vault 本地配置和正文仍不被安装器覆盖。

切换顺序：

1. 同步架构、scaffold 和 skill 契约。
2. 实现并验证来源覆盖审计。
3. 补齐全部长期 Raw 和必要 Routine 到 Wiki 的链接。
4. 收缩 Ingest 和 Lint。
5. 最后把 Query 搜索范围切换为 Wiki-only。
6. 运行完整 fixture，再通过安装器部署当前 checkout。

验收：

- `bash tests/run.sh` 一次通过全部核心检查。
- 测试不读取父 vault 个人正文，不产生缓存或持久运行状态。
- 切换后用至少 3 个真实问题验证：技术来源、项目决策和个人上下文均能先命中 Wiki，再按需到达证据。
- 如果覆盖基线不足，不提前关闭 Query 的现有检索路径。

## P1：清理仓库契约漂移

目标：让 README、安装说明、目录说明和实际导出产物一一对应。

需要改动：

- README 只保留项目入口、最短安装路径和测试入口；安装细节归 `install/README.md`。
- 清理仓库 `.gitignore` 中已失效的目录规则。
- 核对 `community-plugins.json`：默认列表只保留核心流程必需插件，可选插件不作为默认启用项。
- 删除 skill 收缩后失效的脚本参数、文档示例、兼容分支和重复说明。

验收：

- 文档中的仓库路径均真实存在，或明确标记为安装后父 vault 路径。
- 安装器帮助、README 和实际产物列表一致。
- 同一事实只在职责最近的文档中完整说明，其他位置只保留入口。

## P2：精简可选论文总结能力

目标：稳定地产生单篇来源总结，使其成为 Wiki 可引用的 Raw 证据，不让 paper skill 直接维护跨论文 Wiki。

需要改动：

- 将具身智能术语表移出通用 paper skill；领域术语属于父 vault 本地上下文。
- 评估把校验与最终状态写入合并为一个 finalize 命令；只有能删除现有步骤时才实施。
- 为 `--no-parse` 准备流程和 summary 校验增加轻量 fixture；完整 Docling 解析保留为人工集成检查。
- 保持单篇总结来源忠实，并提供稳定标题或路径供 Wiki wikilink 引用。
- 不增加自动联网补 metadata、模型下载器、论文推荐或跨论文 Wiki 写入。

验收：

- 可选 skill 保持领域中立，主流程命令数量不增加。
- 默认测试不要求 GPU、模型 artifacts 或网络。
- 论文产物仍只进入父 vault 的导入工作区、Raw 和 figures；跨论文综合由 Ingest 写入 Wiki。

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

目标：先验证回答质量抽检能否稳定改变 Wiki 的 Ingest / Lint 决策，再决定是否新增 skill。

验证方式：

- 人工选择 3 轮真实问题，对比只读 Wiki 和沿链接补充 Raw / Routine 后的回答。
- 只记录错误引用、缺失 Wiki 承接、断裂来源关系和由此产生的实际维护动作，不建设评分系统。
- 只有当输入、对照方式和输出契约连续稳定，并且结果实际改变维护决策时，才新增最小 `sunday-note-audit` skill。
- 如需固化，第一版只包含 `SKILL.md`，不新增脚本、不写 Wiki、不更新 header、不进入日常 Query / Ingest。

验收：

- 未达到稳定复用门槛时不新增 audit skill。
- Audit 与 `audit_reachability.py` 名称相近但职责明确：前者评估回答证据质量，后者只审计链接图。

## 持续约束

- Query 由语义自然触发，不要求用户显式调用，也不在回答中复述检索机制。
- Wiki 是默认查询入口和知识维护目标；Raw / Routine 是按链接读取的高价值证据层。
- 来源忠实总结留在 Raw；基于一份或多份来源进一步思考形成的结构、关系和稳定结论进入 Wiki；具体目标应用留在 Project。
- 每份长期 Raw 最终都必须有 Wiki backlink；未链接 Raw 由 Lint 持续报告，不通过总 index 或清单 wikilink 制造形式覆盖。
- Query 只搜索 Wiki，不增加 Raw / Routine 回退或扩展 scope；读取 Wiki 后由 agent 自行决定是否读取页面中的链接。
- Journal 默认不摄取、不查询、不 lint；用户明确指定时再处理。
- 不建设全 vault 总索引，不要求所有 Routine 都有 Wiki backlink。
- 不新增向量数据库、Dataview 硬依赖、图数据库、后台自动维护或持久搜索缓存。
- 不新增 `density_score`、`value_score`、`confidence_score` 等主观评分字段。
- 不把 `query_count` 当作自动删除或归档依据。
- 不为 subagent 建通用框架，不把特定运行时参数写成跨 agent 契约。
- 不恢复 Weekly / Monthly 专用脚本；rollup 继续从最小模板创建目标并只维护自动块。
- 不扩展 rollup 或 Query 为任意工作流 DSL；新增配置能力必须来自已出现的真实复用场景。
- 机械检查交给小脚本，语义判断留给 skill 或用户；每项职责只保留一套权威实现。
