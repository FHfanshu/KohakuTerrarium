# 模块

一个 creature 由多个模块组成。本节里，每个模块都有一篇概念文档，结构都一样，共六部分：

1. **它是什么** —— 这个模块在概念上的职责。
2. **为什么需要它** —— 没有它会出什么问题。
3. **我们怎么定义它** —— 它的契约。
4. **我们怎么实现它** —— 内置实现的大致形状，以及要守住的关键不变量。
5. **所以你可以拿它做什么** —— 常见用法，也包括一些不那么直观的用法。
6. **不要被它限制住** —— 这个模块是默认做法，不是铁律。

这六个模块来自[什么是 agent](/concepts/foundations/what-is-an-agent.md)（英文）：

- [Controller](/concepts/modules/controller.md)（英文）—— 推理循环。
- [Input](/concepts/modules/input.md)（英文）—— 第一个触发点。
- [Trigger](/concepts/modules/trigger.md)（英文）—— 从世界到 agent 的唤醒机制。
- [Output](/concepts/modules/output.md)（英文）—— 从 agent 到世界的交付。
- [Tool](/concepts/modules/tool.md)（英文）—— agent 动手做事的方式。
- [Sub-agent](/concepts/modules/sub-agent.md)（英文）—— 受上下文约束的委托者。

另外还有四个横切性的部分。它们不在那六个标准模块里，但表现出来和模块完全一样：

- [Channel](/concepts/modules/channel.md)（英文）—— 通信底层。
- [Plugin](/concepts/modules/plugin.md)（英文）—— 修改模块之间的连接方式。
- [Session and environment](/concepts/modules/session-and-environment.md)（英文）—— 私有状态与共享状态。
- [Memory and compaction](/concepts/modules/memory-and-compaction.md)（英文）—— 把 session 当成可搜索的知识库，以及非阻塞压缩。

这些文档不用按顺序读。挑你会用到的先看，其他可以先跳过。