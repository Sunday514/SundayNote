# Sunday Note 安装器

本目录用于把 SundayNoteAgent 安装到私人 Obsidian vault。

安装器有两种模式：

- 新 vault 初始化：创建标准一级目录骨架、必要 Obsidian 基线配置，并设置工具入口。
- 已有 vault 配置：补建缺失的标准一级目录和工具入口，不移动、重命名或整理已有内容。

安装器设置工具入口和本地默认配置：

```text
.agents/skills/sunday-note-ingest                  -> ../../SundayNoteAgent/skills/sunday-note-ingest
.agents/skills/sunday-note-lint                    -> ../../SundayNoteAgent/skills/sunday-note-lint
.agents/skills/sunday-note-query                   -> ../../SundayNoteAgent/skills/sunday-note-query
.agents/skills/paper-summarizer                    -> ../../SundayNoteAgent/skills/paper-summarizer，可选
.sunday-note-agent/config/sunday-note-vault.yaml
.sunday-note-agent/config/quickadd-rollups.json
.sunday-note-agent/quickadd/                     -> ../SundayNoteAgent/automation/quickadd
.claudian/claudian-settings.json
```

## 使用

在知识库根目录拉下本项目，然后运行安装：

```bash
cd ~/Notes/Sunday-note
git clone git@github.com:Sunday514/SundayNoteAgent.git SundayNoteAgent
bash SundayNoteAgent/install/install.sh
```

本地验证或使用 fork 时：

```bash
mkdir -p /tmp/Sunday-note-test
cd /tmp/Sunday-note-test
git clone /path/to/SundayNoteAgent SundayNoteAgent
bash SundayNoteAgent/install/install.sh
```

如果已经在已有 vault 的 `SundayNoteAgent/` 目录下，可以在外部 vault 根目录运行：

```bash
bash SundayNoteAgent/install/install.sh --vault-root .
```

论文总结是可选组件，依赖可运行 docling 的 Python 环境。需要启用时增加参数：

```bash
bash SundayNoteAgent/install/install.sh --vault-root . --with-paper-summarizer
```

## 生成内容

不带 `--vault-root` 的新 vault 初始化会创建：

- `AGENTS.md`：安装后的私人 vault 根规则。
- `CLAUDE.md`：Claude Code 适配入口。
- `首页.md`：vault 首页。
- `00_导入暂存/`、`10_原始材料/`、`20_每日记录/`、`21_每周记录/`、`22_每月记录/`、`23_项目复盘/`、`30_知识库/`、`40_个人写作/`、`个人模板/`。
- `30_知识库/个人上下文.md`：空的个人上下文 Wiki 页面，`keywords` 初始为空，后续只记录真实兴趣词、方向词、项目词或常用问法。
- 必要 `.obsidian` 基线配置；Obsidian 默认通过 Claudian 调用 agent，workspace 和 Claudian 会话状态由每台设备本地维护。
- `SundayNoteAgent/` 工具层目录。

其中 `00_导入暂存/` 是 PDF、docx、网页导出和解析中间产物的临时导入目录；`40_个人写作/` 只是空目录骨架，安装器不定义其中内容，也不维护其内部结构。

使用 `--vault-root` 配置已有 vault 时，安装器会补建缺失的标准一级目录，但不会创建二级结构，也不会移动、重命名或整理已有内容。它还会设置工具入口：

- 父 vault `.agents/skills/` 下的基础 skill 软链接：`sunday-note-ingest`、`sunday-note-lint`、`sunday-note-query`。
- 传入 `--with-paper-summarizer` 时，额外导出 `paper-summarizer` skill。
- 父 vault `.sunday-note-agent/config/` 下的本地路径配置。
- 父 vault `.sunday-note-agent/config/quickadd-rollups.json` 下的 QuickAdd 统计配置；仅在缺失时创建。
- 父 vault `.sunday-note-agent/quickadd` 软链接，指向 `SundayNoteAgent/automation/quickadd`。
- 父 vault `.claudian/claudian-settings.json` 的脱敏默认配置；仅在缺失时创建。

如果运行前已有 vault 中存在 `30_知识库/`，安装器会在缺失时补建空的 `30_知识库/个人上下文.md`；已有文件不会被覆盖。若 `30_知识库/` 是本次安装新建的目录，则不额外创建个人上下文文件。

安装器只在新 vault 初始化时创建一级目录骨架，不打包个人模板正文，也不预设 Raw 或导入暂存的二级结构。Daily / Weekly / Monthly 模板内容由私人知识库维护；自动化脚本通过 `.sunday-note-agent/config/sunday-note-vault.yaml` 读取模板路径。路径配置是父 vault 本地文件，安装器只在缺失时创建，不会覆盖已有配置。`components.paper_summarizer` 默认使用 `papers` conda 环境，导入工作目录为 `00_导入暂存`，摘要目录为 `10_原始材料`。如果 `.agents/skills/` 下已有同名真实目录，安装器会先移到 `.agents/skills/.replaced-by-symlink/` 再创建软链接，避免删除旧内容。

## Claudian

Claudian（`realclaudian`）是 Obsidian 内默认的 agent 入口。安装器会在缺失时创建 `.claudian/claudian-settings.json`，作为可迁移默认值：

- `providerConfigs.codex.enabled` 为 `true`。
- `providerConfigs.codex.safeMode` 使用 `workspace-write`。
- `providerConfigs.codex.cliPath` 和 `cliPathsByHost` 保持为空，不写 Linux 或 Windows 绝对路径。
- 环境变量、代理、设备 ID、安装方式、会话记录和 tab 状态不进入本仓库配置。

每台设备都需要在自己的系统环境里安装所使用 provider 的 CLI，例如 Codex 用 `codex`，Claude Code 用 `claude`；也可以在本机 Claudian 设置中配置 CLI 路径。Linux 下如果 Obsidian 从桌面启动后找不到 nvm 安装的命令，应把 CLI 安装到 GUI 进程可见的 PATH，或从已加载环境的 shell 启动 Obsidian。Windows 下使用 PowerShell profile、用户环境变量或 npm 全局安装目录维护 PATH。

跨系统同步时，仍按设备维护以下内容：

- `.obsidian/workspace.json`
- `.obsidian/workspace-mobile.json`
- `.claudian/sessions/`

`workspace.json` 会保存当前打开的 pane、最近文件和插件视图状态，不适合作为跨设备共享配置。使用 Syncthing、Obsidian Sync、Dropbox、OneDrive 或其他文件夹同步时，应排除这些 workspace 文件；如果无法排除，就不要把运行中会保存本机状态的 pane 固定在共享 workspace 里。

## 可选 Terminal

Terminal 插件只作为本机可选工具，不作为 agent 默认入口。需要继续使用 Terminal 时，profile 可以在共享 `.obsidian/plugins/terminal/data.json` 中按 `platforms` 区分系统；`.obsidian/bin/`、terminal wrapper 和固定 terminal pane 仍按设备本地维护。

## QuickAdd 与插件说明

- 当前 v0.1 提供 QuickAdd 自动化脚本与配置基线（`SundayNoteAgent/automation/quickadd` 及导出软链接），不预置 vault 内可直接执行的 QuickAdd choices/actions。
- `automation/quickadd/rollup.js` 是通用统计入口；具体统计项由 `.sunday-note-agent/config/quickadd-rollups.json` 决定。
- vault 本地 QuickAdd choice 可以通过本地 wrapper、URI 或变量传入 `rollup=weekly_checkins` / `rollup=month_pack_checkins` 来选择统计配置。
- 默认统计配置中，周统计按 ISO week 自动推导 7 天 Daily；月统计通过 `week_rule` 配置下辖 ISO weeks，默认按周日所在月份选择。
- 统计脚本只更新已存在目标文档中的自动块；Daily / Weekly / Monthly 等具体文档的创建、模板正文和 QuickAdd choice 由父 vault 本地维护。
- Daily Notes core plugin 只负责日期入口，模板和例行动作建议由 QuickAdd 与 `个人模板/` 组合实现。
- 如果你需要隐藏运行产物目录，可选安装并启用 `OA-file-hider`（不作为安装器硬依赖）。
