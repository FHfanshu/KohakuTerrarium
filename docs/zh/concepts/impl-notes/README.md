# 实现说明

这里放了四篇实现层面的说明，分开讲。并不是说你得先懂这些才能用 KT；只是这些取舍在别处也会反复碰到，先看一眼会更容易理解。

- [非阻塞压缩](non-blocking-compaction.md) —— creature 怎么在不暂停 controller 的情况下，总结自己的历史。
- [流解析器](stream-parser.md) —— 为什么工具会在 LLM 还没说完时就开始跑。
- [Prompt 聚合](prompt-aggregation.md) —— 最终的 system prompt 怎么拼出来（base + tools + hints + topology + named outputs + plugins），以及 `skill_mode` 为什么让你能在“把完整文档一起塞进去”和“按需加载”之间做选择。
- [会话持久化](session-persistence.md) —— 双存储模型（只追加的事件日志 + 对话快照）怎么让一个 `.kohakutr` 同时支持恢复会话、人工搜索和 agent 侧 RAG。

每篇文档都按同一条线来写：*问题 → 考虑过哪些方案 → 我们现在怎么做 → 保住了哪些不变量 → 代码在哪。*
