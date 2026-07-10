---
name: paper-summarizer
description: 从本地 PDF 论文解析正文和图表，整理贡献、方法、实验与局限，并生成以论文标题命名的单篇 Raw 总结。用于论文精读和来源摘要任务；PDF 和全部解析过程产物留在 `.import_files/`，实际引用图像写入 vault 的 assets 图像目录。不用于跨论文 Wiki 沉淀、项目调研报告或方案设计。
---

# Paper Summarizer

## 边界

- PDF、metadata、Docling 输出、候选图像、校验结果和状态全部写入 `.import_files/<paper-slug>/`。
- 最终总结写入 `10_原始材料/<论文标题>.md`。
- 最终总结引用的图像写入 `assets/figures/<paper-slug>/`；未引用图像留在导入工作区。
- 不直接写跨论文 Wiki 或 Project；只可标记后续整合价值。

## 资源

- `assets/summary_template.json`：摘要结构和写作规则。
- `assets/embodied_ai_terminology.json`：仅用于归一论文中实际出现的具身智能术语。
- `scripts/prepare_paper_summary.py`：准备工作区、复制 PDF、写 metadata 并运行 Docling。
- `scripts/validate_summary.py`、`scripts/write_summary_status.py`：把校验和状态写回导入工作区。

## 工作流

1. 从父 vault 根目录运行脚本。读取 `.sunday-note-agent/config/sunday-note-vault.yaml`；缺少配置时使用默认目录。
2. 使用当前 Python 环境；不要猜测或切换 conda 环境。确保该环境已安装 Docling 等依赖。
3. 准备并解析论文：

```bash
python .agents/skills/paper-summarizer/scripts/prepare_paper_summary.py --vault-root . --pdf <paper.pdf>
```

可附加 `--metadata`、`--title`、`--authors`、`--published-at`、`--paper-link` 或 `--code-link`。缺失信息写“未明确”，不要编造。

4. 读取脚本输出的 `metadata_path`、`work_dir`、`parse_dir`、`figure_source_dir`、`figures_dir` 和 `summary_path`，再读取解析正文与图表索引。
5. 按 `assets/summary_template.json` 写入 `summary_path`。直接解释问题、方法、证据和局限，不复述论文目录，不写“本文 / 本节 / 下面整理”等包装语句。
6. 最多选择 2-3 张有助于理解方法或实验的图，从 `figure_source_dir` 复制到 `figures_dir`，并使用从 `summary_path` 指向图像的相对路径；默认形如 `../assets/figures/<paper-slug>/<文件名>`。
7. 校验并更新状态：

```bash
python .agents/skills/paper-summarizer/scripts/validate_summary.py <summary_path> --work-dir <work_dir>
python .agents/skills/paper-summarizer/scripts/write_summary_status.py <summary_path> --work-dir <work_dir>
```

事实性判断只来自解析文本或 metadata。PDF 不存在、Docling 解析失败、模型 artifacts 缺失或校验失败时停止并报告失败步骤；不要把论文产物写入 `SundayNoteAgent/`。
