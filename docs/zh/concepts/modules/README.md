# 模块

一个 creature 是由一组模块拼起来的。这一节里，每个模块各有一篇概念文档，基本都按同一套六段来讲：

1. **它是什么** —— 这个模块负责什么。
2. **为什么要有它** —— 没了它会卡在哪。
3. **怎么定义它** —— 也就是它的契约。
4. **怎么实现它** —— 内置实现长什么样，有哪些不能破的约束。
5. **你能拿它做什么** —— 常规用法，还有一些不那么直觉的用法。
6. **别把它当铁律** —— 它是默认做法，不是唯一做法。

在[什么是 agent](/concepts/foundations/what-is-an-agent.md)（英文）里，推导出了六个核心模块：

- [Controller](/zh/concepts/modules/controller.md) —— 推理循环。
- [Input](/zh/concepts/modules/input.md) —— 第一个触发点。
- [Trigger](/zh/concepts/modules/trigger.md) —— 世界把 agent 唤醒的方式。
- [Output](/zh/concepts/modules/output.md) —— agent 把结果送回世界的方式。
- [Tool](/zh/concepts/modules/tool.md) —— agent 动手做事的手段。
- [Sub-agent](/zh/concepts/modules/sub-agent.md) —— 带着局部上下文出去办事的委托者。

另外还有四块不在那六个标准模块里，但用起来和模块没区别：

- [Channel](/zh/concepts/modules/channel.md) —— 通信底层。
- [Plugin](/zh/concepts/modules/plugin.md) —— 改模块之间的连接方式。
- [Session and environment](/zh/concepts/modules/session-and-environment.md) —— 私有状态和共享状态怎么分。
- [Memory and compaction](/zh/concepts/modules/memory-and-compaction.md) —— 把 session 当可搜索知识库，以及非阻塞 compaction。

这些文档不用按顺序读。先挑你现在会用到的看，别的以后再补。