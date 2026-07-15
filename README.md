# SundayNoteAgent

SundayNoteAgent 是一套用于 Obsidian 知识库的 agent 工具层。它提供安装器、Codex / agent skills、QuickAdd 自动化脚本、固定 vault 布局和最小 Routine 模板，适合放在私人知识库中的 `SundayNoteAgent/` 目录下作为工具层独立 repo 使用。

个人笔记、带具体条目的个人模板、附件、图片、本地 Obsidian 工作流配置和运行状态由父知识库管理，不属于本仓库。

## 安装

在 vault 根目录拉下工具层，然后安装配置和目录骨架：

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
.sunday-note-agent/config/quickadd-rollups.json
.sunday-note-agent/quickadd/                       # 安装器托管副本
.stignore                                          # 保留已有规则并补充工具层和导入目录
个人模板/每日记录.md、每周记录.md、每月记录.md          # Routine 最小骨架
30_知识库/个人上下文.md                          # 空 Wiki 页面，只在缺失时创建
```

重复运行安装器会从 `SundayNoteAgent/` 覆盖根规则、skills、QuickAdd 脚本、Weekly 和 month pack 模板中的同名文件，但保留目标目录中的其他文件。Daily 模板只在缺失时创建。安装器会在父 vault 的 `.stignore` 中补充 `/SundayNoteAgent` 和 `/.import_files`，并保留已有规则。论文总结 skill 首次启用时传入 `--with-paper-summarizer`；启用后普通重跑也会继续更新。统计、Claudian 和 Obsidian 配置是 vault 本地文件，只在缺失时创建。

## 更新

更新工具层后，在父知识库中重新运行安装器即可刷新导出内容：

```bash
cd ~/Notes/MyVault/SundayNoteAgent
git pull --ff-only
cd ..
bash SundayNoteAgent/install/install.sh --vault-root .
```

安装器只部署当前 checkout，不自动执行 Git 操作。

## 目录结构

父 vault 使用固定一级布局，安装器和 skills 直接依赖这些路径：

| 路径 | 角色 | 默认维护边界 |
|---|---|---|
| `首页.md` | 知识库导航入口 | 由父 vault 维护 |
| `.import_files/` | PDF、docx、网页导出、解析产物和临时日志 | 只由导入流程管理 |
| `10_原始材料/` | 论文、书籍、课程等长期来源总结 | 默认只读 |
| `20_每日记录/` | Daily Routine | 改写前确认 |
| `21_每周记录/` | Weekly Routine | 改写前确认 |
| `22_每月记录/` | Monthly Routine | 改写前确认 |
| `23_项目复盘/` | Project Routine | 改写前确认 |
| `30_知识库/` | agent 可维护的长期 Wiki | 按 skills 和根规则维护 |
| `40_个人写作/` | 可选 Journal | 仅用户明确要求时读写 |
| `assets/figures/` | 长期引用图像 | 文档使用相对路径引用 |
| `个人模板/` | 父 vault 本地模板 | 个人内容不回写工具仓库 |
| `SundayNoteAgent/` | 可公开的工具层源码 | 由 Git 和安装器维护 |
| `.agents/` | 安装后的 agent skills | 由安装器托管 |
| `.sunday-note-agent/` | 自动化脚本和功能配置 | 由安装器托管 |
| `.claudian/` | Claudian 本地设置和会话 | 仅部署脱敏默认设置 |
| `.obsidian/` | Obsidian 配置和运行状态 | 仅部署必要基线配置 |

`.import_files/` 是导入流程的临时目录，不属于知识分层。完成整理的长期来源总结进入 `10_原始材料/`，长期引用的图像进入 `assets/figures/`。

工具仓库结构：

```text
AGENTS.md                 # 子项目开发规则
automation/               # QuickAdd 等自动化脚本源文件
config/                   # QuickAdd、Obsidian 和 Claudian 配置源文件
install/                  # 安装器和父知识库 scaffold
migration/                # 可复用知识库迁移辅助工具
skills/                   # Codex / agent skills
templates/                # 无具体条目的 Routine 最小模板
tests/                    # 脱敏 fixture 和统一回归入口
```

`templates/` 保存 Daily、Weekly 和 month pack 的最小结构契约；安装器只在父 vault 对应模板缺失时创建副本，之后由父 vault 添加具体打卡类别和个人内容。`config/claudian/` 保存脱敏的 Claudian 默认配置；`config/layout-snapshots/` 保存手动恢复用的 Obsidian 布局快照，不由安装器自动导出。

Obsidian 内默认使用 Claudian（`realclaudian`）作为 agent 入口，Codex provider 在 Claudian 中启用；各 provider 使用当前设备可见的 CLI 命令或本地 Claudian 设置。共享配置不写系统绝对路径、设备 ID、环境变量或代理；`.obsidian/workspace.json`、`.obsidian/workspace-mobile.json` 和 `.claudian/sessions/` 按设备本地维护；Terminal 插件只作为本机可选工具。

## 相关入口

- [安装器说明](install/README.md)
- [子项目开发规则](AGENTS.md)

## 回归检查

修改安装器、QuickAdd 自动化或 query / lint 脚本后，运行：

```bash
bash tests/run.sh
```

检查只使用 Bash、Node 和 Python 标准运行时，在临时目录中生成脱敏 fixture，验证核心 skill、安装导出、Query/Lint 脚本和 QuickAdd，不读取父 vault。

## 隐私边界

本仓库只保存可复用工具层，不保存个人知识库正文。不要把以下内容提交到 SundayNoteAgent：

- 个人笔记正文
- 带具体条目的个人模板正文
- 私有附件、截图或图片
- token、API key、本机绝对路径
- Obsidian workspace 运行状态
- 一次性调试输出或临时工作记录
