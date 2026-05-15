# Sunday Note

这是一个私人 Sunday Note Obsidian vault。

`SundayNoteAgent/` 是可见的框架 submodule。框架文档、通用模板、skills 源文件和自动化源文件保存在 `SundayNoteAgent/` 下。`.agents/` 是父 vault 的 agent skill 导出目录，`.sunday-note-agent/` 保存 SundayNoteAgent 导出的路径配置和 Obsidian 自动化脚本。个人笔记、日常记录、长期知识正文、个人写作、个人模板和本地 Obsidian 工作流配置由本私人仓库维护。

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
- 私人写作保存在 `40_个人写作/`。
- agent 工作边界见 `AGENTS.md`。
