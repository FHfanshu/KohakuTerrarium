# 实现说明

这里有四篇实现层面的短文，单独放出来讲。不是因为你要先懂这些才能用 KT，而是因为里面的设计取舍也反复出现在别处，拿来当心智模型很有用。

- [非阻塞压缩](/concepts/impl-notes/non-blocking-compaction.md)（英文）— creature 怎么在不暂停 controller 的情况下，总结自己的历史。
- [流解析器](/concepts/impl-notes/stream-parser.md)（英文）— 为什么工具会在 LLM 还没说完时就启动。
- [Prompt 聚合](/concepts/impl-notes/prompt-aggregation.md)（英文）— 最终的 system prompt 怎么拼出来（base + tools + hints + topology + named outputs + plugins），以及为什么 `skill_mode` 让你能在“完整文档一起发” 和 “按需加载”之间选。
- [会话持久化](/concepts/impl-notes/session-persistence.md)（英文）— 双存储模型（只追加的事件日志 + 对话快照）怎么让一个 `.kohakutr` 同时服务于恢复会话、人工搜索和 agent 侧 RAG。

每篇文档都按同一条线展开：*问题 → 考虑过的选项 → 我们怎么做 → 保住了哪些不变量 → 代码里在哪。*
