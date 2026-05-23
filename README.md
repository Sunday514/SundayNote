# SundayNoteAgent

SundayNoteAgent 是一套用于 Obsidian 知识库的 agent 工具层。它提供安装器、Codex / agent skills、QuickAdd 自动化脚本、通用模板、路径配置和框架文档，适合放在私人知识库中的 `SundayNoteAgent/` 目录下作为工具层独立 repo 使用。

个人笔记、个人模板、附件、图片、本地 Obsidian 工作流配置和运行状态由父知识库管理，不属于本仓库。

## 安装

在 vault 根目录拉下工具层，然后安装配置和架构：

```bash
mkdir -p ~/Notes/MyVault
cd ~/Notes/MyVault
git clone git@github.com:Sunday514/SundayNoteAgent.git SundayNoteAgent
bash SundayNoteAgent/install/install.sh
```

在已有知识库中安装：

```bash
cd ~/Notes/MyVault
git clone git@github.com:Sunday514/SundayNoteAgent.git SundayNoteAgent
bash SundayNoteAgent/install/install.sh --vault-root .
```

本地验证或使用 fork 时：

```bash
mkdir -p /tmp/my-vault-test
cd /tmp/my-vault-test
git clone /path/to/SundayNoteAgent SundayNoteAgent
bash SundayNoteAgent/install/install.sh
```

## 安装后内容

安装器会创建父知识库骨架、必要 Obsidian 基线配置，并设置 agent 工具入口：

```text
.agents/skills/                                  -> ../SundayNoteAgent/skills
.sunday-note-agent/config/sunday-note-vault.yaml
.sunday-note-agent/quickadd/                     -> ../SundayNoteAgent/automation/quickadd
```

`skills` 和 `quickadd` 使用软链接，父知识库会直接使用 `SundayNoteAgent/` 中的最新工具源码。路径配置文件是父知识库本地文件，只在不存在时由安装器创建，方便使用者按自己的 vault 目录调整。

## 更新

更新工具层后，在父知识库中重新运行安装器即可刷新导出内容：

```bash
cd ~/Notes/MyVault/SundayNoteAgent
git pull
cd ..
bash SundayNoteAgent/install/install.sh --vault-root .
```

工具层更新在 `SundayNoteAgent/` 内完成，重新运行安装器即可刷新导出内容。

## 目录

```text
AGENTS.md                 # 子项目开发规则
automation/               # QuickAdd 等自动化脚本源文件
config/                   # 路径配置源文件和配置类快照
docs/                     # 框架说明和维护文档
install/                  # 安装器和父知识库 scaffold
migration/                # 可复用知识库迁移辅助工具
scripts/                  # 可复用命令行辅助脚本
skills/                   # Codex / agent skills
templates/                # 可复用通用模板
```

`config/layout-snapshots/` 保存可迁移的 Obsidian 布局快照。`templates/` 只保存通用模板，不保存个人模板正文。

## 文档入口

- [安装器说明](install/README.md)
- [框架架构](docs/architecture.md)
- [目录说明](docs/directory-structure.md)
- [路线图](docs/roadmap.md)
- [子项目开发规则](AGENTS.md)

## 隐私边界

本仓库只保存可复用工具层，不保存个人知识库正文。不要把以下内容提交到 SundayNoteAgent：

- 个人笔记正文
- 个人模板正文
- 私有附件、截图或图片
- token、API key、本机绝对路径
- Obsidian workspace 运行状态
- 一次性调试输出或临时工作记录
