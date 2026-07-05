---
name: paper-summarizer
description: 当任务涉及从本地 PDF 论文生成单篇论文摘要、解析论文正文和图表、整理论文贡献/方法/实验/局限，并把单篇论文总结保存到 Raw 层时使用。PDF 和解析过程进入导入工作区，只处理单篇论文 source 摘要，不用于跨论文技术对比、Wiki 沉淀、项目调研报告或方案设计。
---

# Paper Summarizer

## 边界

- PDF、metadata 和解析过程写入导入工作区：默认 `.import_files/<paper-slug>/`。
- 单篇论文总结写入 Raw：默认 `10_原始材料/<paper-slug>/摘要.md`。
- 跨论文技术对比、方法谱系和选型准则属于 Wiki，不由本 skill 直接写入。
- 带项目目标、约束、决策和下一步计划的调研报告属于 Project，不由本 skill 直接写入。
- 项目验证后的稳定经验需要用户确认后再回写 Wiki。

## 资源

- `assets/summary_template.json`：摘要结构、标题和写作规则。
- `assets/embodied_ai_terminology.json`：具身智能和机器人学习术语归一，仅在论文中出现相关术语时使用。
- `scripts/prepare_paper_summary.py`：创建导入工作区和 Raw 摘要目标、复制 PDF、写入 metadata、运行 docling 解析。
- `scripts/validate_summary.py`：校验最终 `摘要.md` 是否符合模板结构。
- `scripts/write_summary_status.py`：聚合 `_work/status.json`。

## 工作流

1. 从父 vault 根目录运行脚本；不要在 `SundayNoteAgent/` 内写入论文产物。
2. 读取 `.sunday-note-agent/config/sunday-note-vault.yaml`；缺少配置时使用默认导入目录 `.import_files` 和默认 Raw 目录 `10_原始材料`。
3. 用配置中的 conda 环境运行脚本；默认环境名是 `papers`。
4. 准备论文工作区：

```bash
conda run -n papers python .agents/skills/paper-summarizer/scripts/prepare_paper_summary.py --vault-root . --pdf <paper.pdf>
```

可附加 `--metadata <metadata.json>`，或用 `--title`、`--authors`、`--published-at`、`--paper-link`、`--code-link` 补充元数据。缺失元数据时写“未明确”，不要编造。

5. 读取脚本输出的 `paper_dir`、`metadata_path`、`work_dir` 和 `parse_dir`，再读取：
   - `<metadata_path>`
   - `<parse_dir>/main_text.md`
   - `<parse_dir>/figure_index.md`
   - `<parse_dir>/figure_index.json`
   - `<paper_dir>/figures/`
6. 按 `assets/summary_template.json` 写 `<paper_dir>/摘要.md`。
7. 最多选择 2-3 张真正帮助理解方法或实验的图，使用相对路径，例如 `figures/figure-01.png`。
8. 事实性判断必须来自解析文本或 metadata；不明确的信息写“未明确”。
9. 用技术讲解者视角写摘要：直接解释问题、方法、证据和局限；不要用第三视角介绍“本文/这篇文章在讲”。
10. 校验并写状态：

```bash
conda run -n papers python .agents/skills/paper-summarizer/scripts/validate_summary.py <paper_dir>/摘要.md --work-dir <work_dir>
conda run -n papers python .agents/skills/paper-summarizer/scripts/write_summary_status.py <paper_dir> --work-dir <work_dir>
```

## 摘要要求

- 标题使用论文标题；标题缺失时使用 PDF 文件名。
- 标题下方写模板要求的 header 字段：作者、发布时间、论文链接；代码链接只有明确存在时写。
- 核心结论放在 header 之后，用一句话说明最重要贡献、方法抓手和结果。
- 方法部分优先解释核心机制，不机械复述论文目录。
- 实验部分说明任务、数据、基线、指标、关键结果和局限。
- 可加入“后续整合价值”小段，说明这篇论文是否值得进入跨论文对比或项目调研；这只是 Raw 来源材料判断，不直接写 Wiki 或 Project。

## 失败处理

- PDF 不存在、docling 解析失败、模型 artifacts 缺失或校验失败时，停止工作并说明失败步骤。
- 不自动联网下载模型、补元数据或查询论文信息。
- 不把私有论文正文、解析产物或生成摘要写入 `SundayNoteAgent/`。
