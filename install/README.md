# Sunday Note 安装器

本目录用于把 SundayNoteAgent 安装到一个新的私人 Obsidian vault。

安装器不会修改当前 vault，也不会迁移个人文档。它只在目标目录中创建新的 vault 骨架，并把当前项目作为可见 submodule 放到 `SundayNoteAgent/`。安装器会设置三类工具入口：

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

如果知识库根目录还不是 git 仓库，安装器会自动执行 `git init -b main`。如果 `SundayNoteAgent/` 还没有登记为 submodule，安装器会根据该目录的 `origin` 自动写入 `.gitmodules`。

也可以由安装器创建一个新的 vault，并自动添加 `SundayNoteAgent/` submodule：

```bash
bash SundayNoteAgent/install/install.sh ~/Notes/Sunday-note
```

本地验证或使用 fork 时：

```bash
bash SundayNoteAgent/install/install.sh /tmp/Sunday-note-test --framework-repo /path/to/SundayNoteAgent
```

目标目录必须不存在或为空目录。

如果已经手动把本项目拉到外部 vault 的 `SundayNoteAgent/` 目录下，可以在外部 vault 根目录运行：

```bash
bash SundayNoteAgent/install/install.sh --vault-root .
```

## 生成内容

- `AGENTS.md`：安装后的私人 vault 根规则。
- `CLAUDE.md`：Claude Code 适配入口。
- `README.md`：私人 vault 简短说明。
- `首页.md`：vault 首页。
- `10_原始材料/`、`20_每日记录/`、`21_每周记录/`、`22_每月记录/`、`23_项目复盘/`、`30_知识库/`、`40_个人写作/`、`个人模板/`。
- 必要 `.obsidian` 基线配置。
- `SundayNoteAgent/` submodule。
- 父 vault `.agents/skills` 软链接，指向 `SundayNoteAgent/skills`。
- 父 vault `.sunday-note-agent/config/` 下的本地路径配置。
- 父 vault `.sunday-note-agent/quickadd` 软链接，指向 `SundayNoteAgent/automation/quickadd`。

安装器只创建 `个人模板/` 目录，不打包个人模板正文。Daily / Weekly / Monthly 模板内容由私人知识库维护；自动化脚本通过 `.sunday-note-agent/config/sunday-note-vault.yaml` 读取模板路径。路径配置是父 vault 本地文件，安装器只在缺失时创建，不会覆盖已有配置。

## QuickAdd 与插件说明

- 当前 v0.1 提供 QuickAdd 自动化脚本与配置基线（`SundayNoteAgent/automation/quickadd` 及导出软链接），不预置 vault 内可直接执行的 QuickAdd choices/actions。
- Daily Notes core plugin 只负责日期入口，模板和例行动作建议由 QuickAdd 与 `个人模板/` 组合实现。
- 如果你需要隐藏运行产物目录，可选安装并启用 `OA-file-hider`（不作为安装器硬依赖）。

## 导出验证

安装后建议在父 vault 根目录运行：

```bash
ls -l .agents/skills
find -L .agents/skills -maxdepth 3 -name SKILL.md -print
```

预期输出至少包含：

- `skills/sunday-note-ingest/SKILL.md`
- `skills/sunday-note-query/SKILL.md`
- `skills/sunday-note-lint/SKILL.md`

