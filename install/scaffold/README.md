# Sunday Note

这是一个私人 Sunday Note Obsidian vault。

框架文档、skills 源文件和自动化源文件保存在 `SundayNoteAgent/` 下。`.agents/` 是父 vault 的 agent skill 导出目录，`.sunday-note-agent/` 保存 SundayNoteAgent 导出的路径配置和 Obsidian 自动化脚本。个人笔记、日常记录、长期知识正文、个人写作、个人模板和本地 Obsidian 工作流配置由父 vault 自行维护。

更新框架时，在知识库根目录进入 `SundayNoteAgent/` 拉取更新，然后重新运行安装器导出最新配置：

```bash
cd SundayNoteAgent
git pull
cd ..
bash SundayNoteAgent/install/install.sh
```

## 目录结构

```text
首页.md
10_原始材料/
20_每日记录/
21_每周记录/
22_每月记录/
23_项目复盘/
30_知识库/
40_个人写作/
个人模板/
SundayNoteAgent/
```

## 使用

- 临时材料先进入 `10_原始材料/收件箱/`。
- Daily、Weekly、Monthly 和项目状态属于 Routine。
- 长期稳定、可复用的内容进入 `30_知识库/`。
- `40_个人写作/` 是可选个人写作骨架；具体内容和结构由用户自行定义，agent 默认只读。
- Daily Notes core plugin 负责日期入口；实际模板与日/周/月动作由 QuickAdd 和 `个人模板/` 管理。
- 当前 v0.1 仅提供 QuickAdd 配置与脚本基线，不预置可直接运行的 choices/actions。
- Linux 和 Windows 共用 vault 时，Obsidian 内默认通过 Claudian 调用 agent；workspace 和 `.claudian/sessions/` 按设备本地维护。
- agent 工作边界见 `AGENTS.md`。
