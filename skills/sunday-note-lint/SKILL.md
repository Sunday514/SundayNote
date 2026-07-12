---
name: sunday-note-lint
description: 用户要求检查、诊断、清理或修复知识库时使用。
---

# Lint

## 工作流

1. 按固定 vault 布局读取用户指定范围和写入边界。
2. 用 `scripts/lint_headers.py` 检查 Wiki header；用 `scripts/audit_reachability.py` 检查 Wiki 导航及其指向 Raw / Routine 的链接。
3. 阅读报告涉及的 Wiki 页面和直接证据；用户明确指定内容检查时，也阅读该范围。把确定的问题整理为具体任务。
4. 按断链与歧义、header、Wiki 导航、Raw 承接排列任务；同一目标页的问题合并为一个任务。
5. 执行模式下逐项创建 subagent，每项完成后复核文件 diff 并重跑相关检查，再执行下一项。
6. 全部任务结束后，只把已完成的内容新增、合并、重要修订或来源关系修复写入维护日志。

## 模式

- “lint、维护、清理、修复”授权执行普通低风险任务。
- “检查、诊断、输出方案、只读、不要修改”只输出问题、方案和拟发送的 subagent 命令；不创建 subagent，不写维护日志。
- 删除、归档、个人上下文、未确认结论和目标页不明确的任务需要用户确认。
- 无变更、blocked 和纯计划不写维护日志。

## 任务边界

- Raw、Routine 只作为证据读取；Journal、Schema 不进入普通维护范围。
- `wiki_unreachable` 只通过 Wiki 导航关系处理，不把 Raw / Routine 加入 index。
- `raw_unlinked` 交给使用 Ingest 的 subagent；执行前确定一个 Wiki 目标页，来源文件保持不变。
- 只有提炼、合并或改写 Wiki 知识的任务使用 Ingest；header、链接和导航等机械修复按 Lint 任务执行。
- 主 agent 负责任务拆分、调度、复核和最终日志，不直接改写普通 Wiki 正文。
- subagent 只修改任务列出的文件，不修改维护日志；同一文件不会同时出现在多个未完成任务中。

每个任务使用以下可直接发送的命令，不固化运行时参数：

```text
任务：
目标：
写入文件：
证据文件：
允许动作：
禁止动作：
验证命令：
返回内容：
```
