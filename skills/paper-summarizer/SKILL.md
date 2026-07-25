---
name: paper-summarizer
description: 用户要求精读或总结本地 PDF 论文时使用。
---

# Paper Summarizer

## 边界

- PDF、metadata、Docling 输出、候选图像、校验结果和状态全部写入 `.import_files/<paper-slug>/`。
- 最终总结写入 `10_原始材料/<论文标题>.md`。
- 最终总结引用的图像写入 `assets/figures/<paper-slug>/`；未引用图像留在导入工作区。
- 不直接写跨论文 Wiki 或 Project；只可标记后续整合价值。

## 资源

- `assets/summary_template.json`：摘要结构和写作规则。
- `scripts/prepare_paper_summary.py`：准备工作区、复制 PDF、写 metadata 并运行 Docling。
- `scripts/validate_summary.py`：校验证据、metadata、结构和图像，并更新导入状态。

## 工作流

1. 从父 vault 根目录运行脚本，使用固定的 `.import_files`、`10_原始材料` 和 `assets/figures` 目录。
2. 使用当前 Python 环境；不要猜测或切换 conda 环境。确保该环境已安装 Docling 等依赖。
3. 准备并解析论文：

```bash
python .agents/skills/paper-summarizer/scripts/prepare_paper_summary.py --vault-root . --pdf <paper.pdf>
```

可附加 `--metadata`、`--title`、`--authors`、`--published-at`、`--paper-link` 或 `--code-link`。缺失信息写“未明确”，不要编造。

4. 检查 `parse_dir/status.json` 的 health 和 warning，再读取完整的 `parsed.md`、`parsed.json` 与 `figure_index.json`。
5. 按 `assets/summary_template.json` 写入 `summary_path`。直接解释问题、方法、证据和局限，不复述论文目录，不写“本文 / 本节 / 下面整理”等包装语句。
6. 在 `work_dir/summarize/summary_evidence.json` 写入 `{"version":1,"evidence":{"<evidence_key>":[{"page":1,"excerpt":"..."}]}}`。为模板声明的每个 `evidence_key` 提供至少一条记录；摘录必须是对应页 `parsed.json` 中实际出现的 12-300 字符文本。可选 `figure_id` 必须来自同页图像索引。
7. 最多选择 2-3 张有助于理解方法或实验的图，从 `figure_source_dir` 复制到 `figures_dir`，保留候选图文件名，并使用从 `summary_path` 指向图像的相对路径；默认形如 `../assets/figures/<paper-slug>/<文件名>`。
8. 校验并更新状态：

```bash
python .agents/skills/paper-summarizer/scripts/validate_summary.py <summary_path> --work-dir <work_dir>
```

事实性判断只来自解析文本或 metadata。PDF 不存在、Docling 解析失败、模型 artifacts 缺失或校验失败时停止并报告失败步骤；不要把论文产物写入 `SundayNoteAgent/`。
