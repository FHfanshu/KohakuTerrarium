# Controller

## 它是什么

**controller** 是 creature 的推理循环。它从队列里拿事件，调用 LLM 产出响应，把里面的 tool 调用和 sub-agent 调用分发出去，收结果，再决定要不要继续下一轮。

它不是“大脑”。大脑是 LLM。controller 只是那层很薄的代码，让 LLM 不只是答一句，而是真的能持续做事。

## 为什么要有它

LLM 是无状态的：你喂它消息，它回你消息。agent 是有状态的：tool 在跑，sub-agent 会被拉起来，事件会不断进来，turn 也会不断累积。中间总得有东西把两边接上。

没 controller，creature 要么退回成单次往返的聊天机器人，要么每种 agent 设计都得自己糊一层胶水。controller 把“LLM + 循环 + tool”这件事收成一个可复用的底层。

## 怎么定义它

把 contract 压成最短，大概是这样：

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

这里有三个设计点值得单拎出来：

- **单事件锁。** 每个 creature 同一时间只跑一个 LLM turn。trigger 可以照常触发，但不会中断当前 turn，只会先排队。
- **可堆叠批处理。** 一阵子里涌进来的同类事件可以合成一个 turn。比如同一个 tick 里有两个 tool 同时完成。
- **流中途分发 tool。** controller 不会等 LLM 整段说完才触发 tool。见 [impl-notes/stream-parser](/zh/concepts/impl-notes/stream-parser.md)。

## 怎么实现它

主类是 `Controller`（`core/controller.py`）。它持有一个 `asyncio.Queue` 作为事件队列，一个处理 LLM 输出流的解析器状态机，以及对 creature 的 `Registry`、`SubAgentManager`、`Executor` 和 `OutputRouter` 的引用。

几个关键不变量：

- `_processing_lock` 在整个“collect → stream → dispatch → await → loop”期间都会一直持有。
- 不可堆叠事件，比如错误或高优先级信号，会打断当前批次，单独跑一个 turn。
- controller 不直接调用 tool；它把 tool 交给 `Executor`，由后者起 `asyncio.Task`。

## 你能拿它做什么

- **会话中途切 LLM。** 用户命令 `/model` 或 `switch_model` API 都可以原地切 provider。controller 不在乎自己现在连的是谁。
- **动态改 system prompt。** `update_system_prompt(...)` 会在下一轮前追加或替换 prompt；controller 会自动带上。
- **重跑上一轮。** `regenerate_last_response()` 会让 controller 用当前状态重新执行上一次 LLM 调用。
- **从任何地方塞事件。** 所有东西都走事件队列，所以 plugin、tool、外部 Python 代码都可以调用 `agent.inject_event(...)`，controller 会按顺序处理。

## 别把它看得太死

没有 controller 的 creature 说不通，agent 总得有循环。但循环的**形状**不是写死的。`pre_llm_call`、`post_llm_call`、`pre_tool_execute` 这些 plugin hook，足够你从外面改写循环里的每一步，不用去碰 controller 类本身。见 [plugin](/zh/concepts/modules/plugin.md)。

## 另见

- [组合 agent](/zh/concepts/foundations/composing-an-agent.md) —— controller 在整体里的位置。
- [impl-notes/stream-parser](/zh/concepts/impl-notes/stream-parser.md) —— 为什么 tool 会在 LLM 说完前就启动。
- [impl-notes/prompt-aggregation](/zh/concepts/impl-notes/prompt-aggregation.md) —— controller 实际驱动的 prompt 是怎么拼出来的。
- [reference/python.md — Agent, Controller](/zh/reference/python.md) —— 相关签名。