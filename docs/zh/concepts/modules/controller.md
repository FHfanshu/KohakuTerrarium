# Controller（控制器）

## 它是什么

**Controller** 是 creature 的推理循环。它从队列里取出事件，调用 LLM 生成响应，分发返回的工具调用和子 agent 调用，收集结果，再决定是否继续下一轮。

它**不是**“大脑”。大脑是 LLM。Controller 是一层很薄的代码，让 LLM 能在一段时间里持续做事，而不是只回一次。

## 为什么需要它

LLM 是无状态的：你给它消息，它再吐出消息。Agent 是有状态的：工具在运行，子 agent 会被拉起，事件不断到来，轮次也会累积。两者之间总得有个东西接起来。

没有 controller，creature 要么退化成一次性的 LLM 往返，也就是聊天机器人；要么每种 agent 设计都得自己写一套胶水代码。Controller 就是把“LLM + 循环 + 工具”变成可复用底层的那一层，而不是每次临时拼接。

## 我们怎么定义它

把 controller 的约定压缩一下，大概是这样：

```
loop:
    events = collect from queue (batch stackable, break on non-stackable)
    context = build turn input from events
    stream = LLM.chat(messages + context)
    for chunk in stream:
        output text chunks
        dispatch parsed tool / sub-agent / framework-command blocks
    wait for direct-mode tools and sub-agents
    feed their results back as new events
    loop or break
```

这里有三个值得点出来的设计选择：

- **单事件锁。** 每个 creature 同一时间只跑一个 LLM turn。Trigger 可以随时触发，但不会打断当前轮次，只会进队列排队。
- **可堆叠批处理。** 一小段时间内涌入的同类事件会并成一个 turn，比如同一个 tick 里有两个工具完成。
- **流中途分发工具。** Controller 不会等 LLM 把整段话说完才触发工具。见 [impl-notes/stream-parser](/concepts/impl-notes/stream-parser.md)（英文）。

## 我们怎么实现它

主类是 `Controller`（`core/controller.py`）。它持有一个用于事件的 `asyncio.Queue`、一个处理 LLM 输出流的解析器状态机，以及对 creature 的 `Registry`（工具）、`SubAgentManager`、`Executor` 和 `OutputRouter` 的引用。

几个关键不变量：

- `_processing_lock` 会在整个“collect → stream → dispatch → await → loop”过程中一直持有。
- 不可堆叠事件，比如错误和高优先级信号，会打断当前批次，单独占用一个 turn。
- Controller 从不直接调用工具；它把工具交给 `Executor`，由后者生成 `asyncio.Task`。

## 因而你能做什么

- **在会话中途切换 LLM。** 用户命令 `/model` 或 `switch_model` API 会原地切换 LLM provider。Controller 不关心自己在跟哪一家 provider 说话。
- **动态修改 system prompt。** `update_system_prompt(...)` 会在下一轮之前追加或替换 prompt；controller 会自动用上新内容。
- **重新生成某一轮。** `regenerate_last_response()` 会让 controller 用当前状态重新执行上一次 LLM 调用。
- **从任何地方注入事件。** 所有东西都走事件队列，所以插件、工具或外部 Python 代码都可以调用 `agent.inject_event(...)`，controller 会按顺序处理。

## 别被它框住

没有 controller 的 creature 说不通——agent 不可能没有循环。但循环的**形状**可以改。插件钩子 `pre_llm_call`、`post_llm_call`、`pre_tool_execute` 等，允许你从外部改写循环里的每一步，不用去碰 controller 类本身。见 [plugin](/concepts/modules/plugin.md)（英文）。

## 另见

- [组合 agent](/concepts/foundations/composing-an-agent.md)（英文）——controller 在整体里的位置。
- [impl-notes/stream-parser](/concepts/impl-notes/stream-parser.md)（英文）——为什么工具会在 LLM 停下之前就启动。
- [impl-notes/prompt-aggregation](/concepts/impl-notes/prompt-aggregation.md)（英文）——controller 实际在驱动什么 prompt。
- [reference/python.md — Agent, Controller](/reference/python.md)（英文）——相关签名。
