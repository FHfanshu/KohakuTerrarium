# 模块

一个 creature 就是几块东西拼起来一起跑。这一节里，每个模块都有单独的说明，基本都按这六个问题来讲：

1. **它是什么** —— 这个模块负责什么。
2. **为什么要有它** —— 没了它会卡在哪。
3. **怎么定义它** —— 对外要满足什么。
4. **怎么实现它** —— 内置实现长什么样，有哪些不能破的约束。
5. **你能拿它做什么** —— 常规用法，也包括一些乍看不太像它该做的事。
6. **别把它看得太死** —— 这是默认做法，不是唯一做法。

在[什么是 agent](/concepts/foundations/what-is-an-agent.md)里，会一路讲到六个核心模块：

- [Controller](/zh/concepts/modules/controller.md) —— 推理循环。
- [Input](/zh/concepts/modules/input.md) —— 第一个触发点。
- [Trigger](/zh/concepts/modules/trigger.md) —— 世界把 agent 唤醒的方式。
- [Output](/zh/concepts/modules/output.md) —— agent 把结果送回世界的方式。
- [Tool](/zh/concepts/modules/tool.md) —— agent 动手做事的手段。
- [Sub-agent](/zh/concepts/modules/sub-agent.md) —— 带着一小段上下文出去单干的子 agent。

另外还有四块不在那六个核心模块里，但平时用起来跟模块没什么区别：

- [Channel](/zh/concepts/modules/channel.md) —— 通信底层。
- [Plugin](/zh/concepts/modules/plugin.md) —— 改模块之间的连接方式。
- [Session and environment](/zh/concepts/modules/session-and-environment.md) —— 私有状态和共享状态怎么分。
- [Memory and compaction](/zh/concepts/modules/memory-and-compaction.md) —— 把 session 当可搜索知识库，以及非阻塞 compaction。

这些文档不用按顺序读。先挑你现在会用到的看，别的以后再补。