---
name: sunday-note-ingest
description: 将用户指定的 Raw、Routine、Project 或已确认对话中的稳定知识提炼并写入 Wiki。用于用户要求 ingest、摄取资料、沉淀知识、把来源总结编译进 Wiki，或将新知识合并到已有主题页时。
---

# Ingest

## 工作流

1. 读取 vault 路径配置、用户指定的 Raw / Routine、已确认对话和相关 Wiki 页面；只在 Wiki 范围内查找同主题页面。
2. 判断材料能否提高未来检索效率、回答深度、独特见解或知识结构化程度。没有知识增量时不写文件，并说明原因。
3. 优先合并到已有同主题页面；只为独立、稳定、可复用的主题新建 Wiki 页面。Raw 和 Routine 保持不变。
4. 区分来源事实、agent 推断、项目结论和用户确认信息，只写入有依据的稳定知识。在相关知识附近保留实际读取的 Raw / Routine wikilink。
5. 根据实际改动更新 Wiki header、必要的 index 和维护日志。
6. 简述修改的页面和来源关系；列出仍需用户确认的事项。

## Wiki 写作契约

- 围绕一个稳定主题组织页面；新页面包含标题、完整 Wiki header 和承载知识所需的小节。
- 按概念、关系或结论组织正文；标题直接表达内容，开头简述主题范围或核心结论。
- 写入可独立作为回答上下文的知识，并保留理解结论所需的条件、边界和关键依据。
- 沿用已有页面的有效结构，把增量合并到最相关的位置；不要为统一格式重写整页。
- 不写处理过程、材料清单、任务计划、agent 注释或无法确认的推断。

## Header、index 和 log

- 已有页面的正文或来源发生实质变化时，将 `last_updated` 写为当天，`update_count` 每页每轮加 1，并在 `sources` 中汇总、去重本轮实际使用的来源。
- 保持已有 `topic` 稳定；只在有检索价值时调整 `keywords`。保留 Query 维护的 `last_queried` 和 `query_count`。
- 新页面创建完整 header：`last_updated` 写当天，`update_count: 1`，`last_queried: ""`，`query_count: 0`，并填写实际 `sources`、单一稳定 `topic` 和真实检索词 `keywords`。
- 只链接实际读取且路径已确认的文档，不推测链接或来源。
- 正文没有变化时不更新 header、index 或维护日志。
- 只有核心 Wiki 导航发生变化时才更新 index；只有真实内容新增、合并、重要修订或来源关系修复时才按现有格式更新维护日志。

## 写入边界

- 用户明确调用 Ingest 即授权普通 Wiki 正文及其必要 header、index 和维护日志写入。
- 涉及个人上下文、删除、归档或未确认结论时，写入前请求确认。
- 一轮可能修改多个 Wiki 页面时，先列出全部目标页面并统一确认范围。
- 不触发 Query、Lint、全 vault 审计或外部搜索。
