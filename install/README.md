# Sunday Note 安装器

本目录用于把 SundayNoteAgent 安装到私人 Obsidian vault。

安装器有两种模式：

- 新 vault 初始化：创建标准目录骨架、必要 Obsidian 基线配置，并设置工具入口。
- 已有 vault 配置：只写入缺失的入口文件和工具链接，不创建或调整内容层目录结构。

安装器设置三类工具入口：

```text
.agents/skills/                                  -> ../SundayNoteAgent/skills
.sunday-note-agent/config/sunday-note-vault.yaml
.sunday-note-agent/quickadd/                     -> ../SundayNoteAgent/automation/quickadd
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

## 生成内容

不带 `--vault-root` 的新 vault 初始化会创建：

- `AGENTS.md`：安装后的私人 vault 根规则。
- `CLAUDE.md`：Claude Code 适配入口。
- `README.md`：私人 vault 简短说明。
- `首页.md`：vault 首页。
- `10_原始材料/`、`20_每日记录/`、`21_每周记录/`、`22_每月记录/`、`23_项目复盘/`、`30_知识库/`、`40_个人写作/`、`个人模板/`。
- 必要 `.obsidian` 基线配置；terminal wrapper 和 workspace 运行状态由每台设备本地维护。
- `SundayNoteAgent/` 工具层目录。

其中 `40_个人写作/` 只是空目录骨架，安装器不定义其中内容，也不维护其内部结构。

使用 `--vault-root` 配置已有 vault 时，安装器不会补建、移动、重命名或整理上述内容层目录，只设置工具入口：

- 父 vault `.agents/skills` 软链接，指向 `SundayNoteAgent/skills`。
- 父 vault `.sunday-note-agent/config/` 下的本地路径配置。
- 父 vault `.sunday-note-agent/quickadd` 软链接，指向 `SundayNoteAgent/automation/quickadd`。

安装器只在新 vault 初始化时创建 `个人模板/` 目录，不打包个人模板正文。Daily / Weekly / Monthly 模板内容由私人知识库维护；自动化脚本通过 `.sunday-note-agent/config/sunday-note-vault.yaml` 读取模板路径。路径配置是父 vault 本地文件，安装器只在缺失时创建，不会覆盖已有配置。

## 跨设备 terminal

Obsidian terminal 插件支持多个 terminal profile。跨 Linux 和 Windows 同步 vault 时，可以共享 `.obsidian/plugins/terminal/data.json`，但要在同一个配置里放多套 profile，并用 `platforms` 限定适用系统。

profile 示例：

```json
{
  "name": "Bash",
  "type": "integrated",
  "executable": "/bin/bash",
  "args": ["-lc", "exec /bin/bash"],
  "platforms": {
    "linux": true
  }
}
```

```json
{
  "name": "PowerShell",
  "type": "integrated",
  "executable": "powershell",
  "args": ["-NoLogo"],
  "platforms": {
    "windows": true
  }
}
```

也可以把 Windows profile 改成 Git Bash 或 WSL，例如 `executable` 使用 `wsl`，或使用 Git Bash 的 `bash.exe` 路径。不要在共享 profile 里引用 `.obsidian/bin/` 下的 wrapper；wrapper 是系统相关脚本，应按设备本地维护。

跨系统同步时，仍按设备维护以下内容：

- `.obsidian/workspace.json`
- `.obsidian/workspace-mobile.json`
- `.obsidian/bin/`

`workspace.json` 会保存已经打开的 terminal pane 和具体 profile 引用，容易把 Linux pane 带到 Windows。父 vault 如果使用 Git 管理，安装器生成的 `.gitignore` 已默认忽略这些本地状态路径。使用 Obsidian Sync、Syncthing、Dropbox、OneDrive 或其他文件夹同步时，也应在对应同步工具里排除这些路径。

## QuickAdd 与插件说明

- 当前 v0.1 提供 QuickAdd 自动化脚本与配置基线（`SundayNoteAgent/automation/quickadd` 及导出软链接），不预置 vault 内可直接执行的 QuickAdd choices/actions。
- Daily Notes core plugin 只负责日期入口，模板和例行动作建议由 QuickAdd 与 `个人模板/` 组合实现。
- 如果你需要隐藏运行产物目录，可选安装并启用 `OA-file-hider`（不作为安装器硬依赖）。
