# Sunday Note 安装器

本目录用于把 SundayNoteAgent 安装到私人 Obsidian vault。

同一脚本同时用于首次安装和更新：补建缺失的 vault 骨架和本地基线文件，并用当前 checkout 覆盖安装器托管内容。它不移动、重命名或整理已有个人内容，也不自动执行 Git 操作。

安装器设置工具入口和本地默认配置：

```text
.agents/skills/sunday-note-ingest                  # 安装器托管副本
.agents/skills/sunday-note-lint                    # 安装器托管副本
.agents/skills/sunday-note-query                   # 安装器托管副本
.agents/skills/paper-summarizer                    # 安装器托管副本，可选
.sunday-note-agent/config/quickadd-rollups.json
.sunday-note-agent/quickadd/                       # 安装器托管副本
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

安装器会创建缺失的：

- `AGENTS.md`：安装后的私人 vault 根规则。
- `首页.md`：vault 首页。
- `.import_files/`：隐藏导入工作目录。
- `10_原始材料/`、`20_每日记录/`、`21_每周记录/`、`22_每月记录/`、`23_项目复盘/`、`30_知识库/`、`40_个人写作/`、`个人模板/`。
- `个人模板/每日记录.md`、`周记录.md`、`月记录.md`：无具体打卡项的最小 Routine 骨架，只在缺失时创建。
- `30_知识库/个人上下文.md`：空的个人上下文 Wiki 页面，`keywords` 初始为空，后续只记录真实兴趣词、方向词、项目词或常用问法。
- `.obsidian/community-plugins.json` 基线；Obsidian 默认通过 Claudian 调用 agent，workspace 和 Claudian 会话状态由每台设备本地维护。
- `.stignore`：保留已有规则并补充 `/SundayNoteAgent` 和 `/.import_files`，避免工具仓库与导入中间产物进入 Syncthing 同步。
- `SundayNoteAgent/` 工具层目录。

其中 `.import_files/` 是 PDF、docx、网页导出和解析中间产物的临时导入目录；`40_个人写作/` 只是空目录骨架，安装器不定义其中内容，也不维护其内部结构。

不论是新 vault 还是已有 vault，安装器都会补建缺失的标准一级目录和 `.import_files/`，但不创建二级结构，也不整理已有内容。工具入口的维护方式是：

- 每次覆盖父 vault 的 `AGENTS.md`、三个基础 skill 和 `.sunday-note-agent/quickadd/` 中的同名源文件。
- 传入 `--with-paper-summarizer` 时首次导出 `paper-summarizer`；已导出时，普通重跑也会刷新它。
- 托管目录中不与源仓库同名的额外文件会保留。
- 父 vault `.sunday-note-agent/config/quickadd-rollups.json` 下的 QuickAdd 统计配置；仅在缺失时创建。
- 父 vault `.claudian/claudian-settings.json` 的脱敏默认配置；仅在缺失时创建。
- 父 vault `.stignore` 保留已有内容，每次安装确保包含根目录规则 `/SundayNoteAgent` 和 `/.import_files`。

只要 `30_知识库/个人上下文.md` 缺失，安装器就创建空 scaffold；已有文件不会被覆盖。

项目模板只保存稳定结构和自动块标记，不包含具体打卡类别或个人正文。父 vault 的模板副本创建后不再覆盖；自动化脚本使用固定的 Routine 和模板路径。论文总结脚本使用当前 Python 环境，导入工作目录为 `.import_files`，摘要目录为 `10_原始材料`。

## 知识流

- Ingest 从用户指定的 Raw、Routine 或已确认对话中提炼稳定知识，只写入 Wiki，并保留实际来源链接。
- Query 只搜索 Wiki；Wiki 证据不足时，只沿页面中的直接链接按需读取 Raw / Routine。
- Lint 使用 `lint_headers.py` 检查 Wiki header，使用 `audit_reachability.py` 检查 Wiki 导航、Raw backlink 和已有 Routine 证据链接；诊断模式保持只读。

安装器覆盖三个核心 skill 及其同名源文件，保留托管目录中的额外文件。父 vault 的配置、模板和内容不进入托管覆盖范围。

## 验证

在工具仓库根目录运行：

```bash
bash tests/run.sh
```

该命令使用临时 vault 验证首次安装、托管文件更新、重复安装、核心 skill 导出和安装后脚本运行，不读取实际父 vault。

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

- 当前 v0.1 提供 QuickAdd 自动化脚本与配置基线（`SundayNoteAgent/automation/quickadd` 及安装器托管副本），不预置 vault 内可直接执行的 QuickAdd choices/actions。
- `automation/quickadd/rollup.js` 是通用统计入口；具体统计项由 `.sunday-note-agent/config/quickadd-rollups.json` 决定。
- vault 本地 QuickAdd choice 可以通过本地 wrapper、URI 或变量传入 `rollup=weekly_checkins` / `rollup=month_pack_checkins` 来选择统计配置。
- 默认统计配置中，周统计按 ISO week 自动推导 7 天 Daily；month pack 包含周日落在该自然月的 ISO weeks。
- 周或 month pack 目标缺失时，统计脚本先从配置的最小模板创建文档，再更新自动块；Daily 创建和 QuickAdd choice 仍由父 vault 本地维护。
- 安装器不覆盖已有 `quickadd-rollups.json`；旧 vault 需手动合并默认配置中的 `target.template` 才会启用缺失目标创建。
- Daily Notes core plugin 只负责日期入口，模板和例行动作建议由 QuickAdd 与 `个人模板/` 组合实现。
- 如果你需要隐藏运行产物目录，可选安装并启用 `OA-file-hider`（不作为安装器硬依赖）。
