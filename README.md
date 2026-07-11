# SundayNoteAgent

SundayNoteAgent 是一套用于 Obsidian 知识库的 agent 工具层。它提供安装器、Codex / agent skills、QuickAdd 自动化脚本、路径配置和框架文档，适合放在私人知识库中的 `SundayNoteAgent/` 目录下作为工具层独立 repo 使用。

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

需要启用论文总结时，在安装命令中增加可选组件：

```bash
bash SundayNoteAgent/install/install.sh --vault-root . --with-paper-summarizer
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
.agents/skills/sunday-note-ingest                  # 安装器托管副本
.agents/skills/sunday-note-lint                    # 安装器托管副本
.agents/skills/sunday-note-query                   # 安装器托管副本
.agents/skills/paper-summarizer                    # 安装器托管副本，可选
.sunday-note-agent/config/sunday-note-vault.yaml
.sunday-note-agent/config/quickadd-rollups.json
.sunday-note-agent/quickadd/                       # 安装器托管副本
30_知识库/个人上下文.md                          # 空 Wiki 页面，只在缺失时创建
```

重复运行安装器会从 `SundayNoteAgent/` 覆盖根规则、skills 和 QuickAdd 脚本中的同名文件，但保留目标目录中的其他文件。论文总结 skill 首次启用时传入 `--with-paper-summarizer`；启用后普通重跑也会继续更新。路径、统计、Claudian 和 Obsidian 配置是 vault 本地文件，只在缺失时创建。

## 更新

更新工具层后，在父知识库中重新运行安装器即可刷新导出内容：

```bash
cd ~/Notes/MyVault/SundayNoteAgent
git pull --ff-only
cd ..
bash SundayNoteAgent/install/install.sh --vault-root .
```

安装器只部署当前 checkout，不自动执行 Git 操作。

## 目录

```text
AGENTS.md                 # 子项目开发规则
automation/               # QuickAdd 等自动化脚本源文件
config/                   # 路径配置源文件和配置类快照
docs/                     # 框架说明和维护文档
install/                  # 安装器和父知识库 scaffold
migration/                # 可复用知识库迁移辅助工具
skills/                   # Codex / agent skills
```

`config/claudian/` 保存脱敏的 Claudian 默认配置；其中不包含设备 ID、CLI 绝对路径、环境变量、代理或会话状态。`config/layout-snapshots/` 保存手动恢复用的 Obsidian 布局快照，不由安装器自动导出。当前不提供通用笔记模板。

Obsidian 内默认使用 Claudian（`realclaudian`）作为 agent 入口，Codex provider 在 Claudian 中启用；各 provider 使用当前设备可见的 CLI 命令或本地 Claudian 设置。共享配置不写系统绝对路径、设备 ID、环境变量或代理；`.obsidian/workspace.json`、`.obsidian/workspace-mobile.json` 和 `.claudian/sessions/` 按设备本地维护；Terminal 插件只作为本机可选工具。

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
