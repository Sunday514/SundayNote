---
last_updated: "2026-07-06"
update_count: 4
last_queried: ""
query_count: 0
sources:
  - "[[AGENTS]]"
topic: "Sunday Note 目录结构"
keywords:
  - "目录结构"
  - "信息架构"
  - "Raw"
  - "Routine"
  - "Wiki"
  - "Journal"
  - "Schema"
  - "路径映射"
  - "导入工作区"
---

# 目录说明

本 vault 的一级架构目录按用途编号；`.import_files/` 是隐藏导入工作目录，不属于知识分层或编号体系。`SundayNoteAgent/` 是维护目录，不参与内容层编号。

## 编号逻辑

- `首页.md`: Schema，知识库导航入口。
- `10_原始材料/`: Raw，长期可读来源材料层。
- `20_每日记录/`: Routine，当天视图。
- `21_每周记录/`: Routine，每周视图。
- `22_每月记录/`: Routine，每月视图。
- `23_项目复盘/`: Routine，项目视图。
- `30_知识库/`: Wiki，长期记忆层。
- `40_个人写作/`: Journal，可选个人写作骨架；具体内容和结构由用户自行定义。
- `个人模板/`: Schema，本地个人模板和相关自动化配置。
- `SundayNoteAgent/`: Schema，可公开的工具项目，保存框架文档、skills、自动化脚本、配置快照、迁移工具和辅助文件。
- `.agents/`: Schema，agent skill 导出目录。
- `.sunday-note-agent/`: Schema，路径配置和自动化导出目录。
- `.claudian/`: Schema，Claudian 本地设置和会话状态；只维护脱敏默认设置，不维护会话。
- `.obsidian/`: Schema，Obsidian 配置和运行状态；只维护明确需要迁移的配置。

## 信息架构

```text
Raw = 证据
Routine = 例行
Wiki = 记忆
Journal = 写作
Schema = 规则
```

`.import_files/` 不是知识分层。不可直接长期引用的导入文件先放入这个隐藏目录；转换后的 Markdown 来源材料进入 Raw。

Routine 是用户主导的过程记录层，不等同于“工作”。Daily、Weekly、Monthly 和 Project 是 Routine 内部的不同视图。agent 写入或改写 Routine 前需要确认。

`40_个人写作/` 不属于自动编译链路。SundayNoteAgent 不定义其中内容，也不维护其内部结构；只有用户明确确认时，agent 才能基于其中内容提出知识沉淀建议。

Raw 保存已转换成 Obsidian / LLM 可读形态的来源材料，例如论文总结、读书笔记、课程转写和网页整理稿。Wiki 是 agent 可维护的长期记忆层。Wiki 页面使用 YAML header 记录 `last_updated`、`update_count`、`last_queried`、`query_count`、`sources`、`topic` 和 `keywords`，用于 query、ingest 和 lint 判断时效、维护次数、使用次数、来源、主题归属和检索入口。`30_知识库/个人上下文.md` 属于本地 Wiki，用于保存长期兴趣、近期计划、推荐偏好和当前项目，不放入 `SundayNoteAgent/`。

论文整理按信息层分工：PDF 原文和全部解析过程产物进入 `.import_files/`；单篇论文总结以 `10_原始材料/<论文标题>.md` 保存，引用图像进入 `assets/figures/`；跨论文技术对比、方法谱系和选型准则进入 Wiki；带具体项目目标、约束、决策和下一步计划的调研报告或方案设计进入 `23_项目复盘/`。项目验证后沉淀出的稳定经验再回写 Wiki。

## 框架与个人内容

框架项目由 `AGENTS.md`、`CLAUDE.md`、`SundayNoteAgent/`、`首页.md`、本地模板、必要 Obsidian 配置和脱敏 Claudian 默认配置组成。`SundayNoteAgent/` 是可公开的工具项目，不保存个人内容、个人模板正文或本地运行状态。

`SundayNoteAgent/config/sunday-note-vault.yaml` 保存机器可读的目录映射默认值；安装器会在父 vault 缺少配置时创建 `.sunday-note-agent/config/sunday-note-vault.yaml`。人读文档仍直接使用当前目录名；skills 和未来脚本优先读取父 vault `.sunday-note-agent/` 下的本地配置，避免把 Raw、Wiki 等语义层和中文目录名绑定。`.import_files/` 使用独立路径配置，不属于 `layers`。

`30_知识库/索引.md`、`30_知识库/知识库维护日志.md` 和个人上下文页面属于本地 Wiki 维护文件。索引是核心导航入口，不重复 header 信息；维护日志记录 ingest / query / lint 带来的状态变化；个人上下文集中保存能降低 agent 沟通成本的稳定个人偏好和计划。这些文件默认不进入 Git。

必要 Obsidian 配置是可迁移基线，不是插件安装包。仓库保存 `config/` 下的框架级配置、脱敏 Claudian 默认配置和布局快照，不保存社区插件的 `main.js`、`manifest.json`、`styles.css`，也不保存 Daily Notes、Calendar、Templates、QuickAdd actions、terminal wrapper、workspace、Claudian sessions、设备 ID、CLI 绝对路径、环境变量或代理等本地配置。Obsidian 内默认通过 Claudian（`realclaudian`）调用 agent，Codex provider 使用当前设备可见的 `codex` 命令或本机 Claudian 设置。恢复 `config/layout-snapshots/` 中的布局快照前，用户需要先在 Obsidian 中安装并启用必备插件。

QuickAdd 是模板、捕获和例行维护动作的主要入口。创建 Daily、Weekly、Monthly 等具体文档的动作配置属于父 vault 本地模板配置；本仓库只提供可复用统计入口 `SundayNoteAgent/automation/quickadd/rollup.js`。统计项由父 vault `.sunday-note-agent/config/quickadd-rollups.json` 配置；默认配置中，周统计按 ISO week 自动推导 7 天 Daily，月统计通过 `week_rule` 配置下辖 ISO weeks，默认按周日所在月份选择。统计脚本只更新已存在目标文档中的自动块，不负责创建、移动或维护周/月记录正文。

具体打卡项保存在本地 Daily 模板中。Daily 创建统一使用个人模板中的 `每日记录.md`；某天不参与统计的项目可以直接从当天 Daily 中删除。Weekly 统计优先按 Daily 模板中的 checkbox 顺序输出，同时兼容历史 Daily 中额外出现的打卡项。

当前不提供通用笔记模板。`SundayNoteAgent/templates/` 只保留占位，不维护 Wiki、论文、书籍或课程模板。`个人模板/` 保存 Daily / Weekly / Monthly 等个人模板正文，由私人知识库管理。Templater 可以作为可选增强，但不作为迁移必需依赖。

`SundayNoteAgent/migration/` 保存可复用的知识库迁移辅助工具，例如从外部知识源导出导入工作区文件或转换成 Raw 来源材料。迁移工具不得保存密钥、个人正文或一次性运行状态。

## 图像归属

图像文件统一放在 vault 根目录的 `assets/figures/` 下。无法确认归属的临时图片先放入 `.import_files/`。

## 常用入口

- Agent 规则: [[AGENTS]]
- 架构设计: [[architecture]]
- 未来待办: [[roadmap]]
- Agent skills 源文件: `SundayNoteAgent/skills/`
- 命令行辅助脚本: `SundayNoteAgent/scripts/`
- 迁移辅助工具: `SundayNoteAgent/migration/`
- QuickAdd 自动化源文件: `SundayNoteAgent/automation/quickadd/`
- 安装后 skill 发现入口: `.agents/skills/`，其中每个 skill 软链接到 `SundayNoteAgent/skills/<skill-name>/`
