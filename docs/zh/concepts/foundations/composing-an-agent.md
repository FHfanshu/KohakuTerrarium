# 如何组合一个 agent

[什么是 agent](what-is-an-agent.md) 里介绍了六个模块。这一页讲的是，它们在运行中的 creature 里到底怎么拼起来。

## 统一信封：`TriggerEvent`

所有来自 controller 外部的东西，进来时都会变成一个 `TriggerEvent`：

- 用户输入 → `TriggerEvent(type="user_input", content=...)`
- 定时器触发 → `TriggerEvent(type="timer", ...)`
- tool 执行完成 → `TriggerEvent(type="tool_complete", job_id=..., content=...)`
- sub-agent 返回 → `TriggerEvent(type="subagent_output", ...)`
- channel 消息 → `TriggerEvent(type="channel_message", ...)`
- 上下文注入 → `TriggerEvent(type="context_update", ...)`
- 错误 → `TriggerEvent(type="error", stackable=False, ...)`

所有来源都用同一种封装。controller 不需要为每种来源各写一套代码路径；它只要问一句：“这一轮我手里有哪些事件？” 架构上的简化，核心就在这。

## 事件队列

```
        +-----------+  +---------+  +-----------+  +----------+
        | input.get |  | trigger |  | tool done |  | sub done |
        +-----+-----+  +----+----+  +-----+-----+  +-----+----+
              \             \             /             /
               \             \           /             /
                +------------ event queue ------------+
                              |
                              v
                        +------------+
                        | Controller |
                        +------------+
```

所有唤醒来源都会把事件推到同一个队列里。那些“差不多同时”到达的多个事件，可以是 **stackable** 的——controller 会把它们合并进同一轮用户消息里，这样一阵密集活动不会变成一阵密集的 LLM 调用。

不能叠的事件，比如错误或高优先级信号，就会打断这一批，单独占一轮处理。

## 一轮是怎么跑完的

```
  +---- collect events from queue (batch stackable)
  |
  |   +- build turn context (job status + event content, multimodal-aware)
  |
  |   +- call LLM in streaming mode
  |
  |       during stream:
  |         - text chunks -> output
  |         - tool blocks detected -> asyncio.create_task(run tool)
  |         - sub-agent blocks detected -> asyncio.create_task(run sub)
  |         - framework commands (info, jobs, wait) -> inline
  |
  |   +- await direct-mode tools + sub-agents
  |
  |   +- feed their results back as new events
  |
  |   +- decide: loop or break
  +---- back to event queue
```

这里有几条很关键的约束：

1. **tool 会立刻启动。** 一个 tool block 刚解析完，还没等 LLM 把整段话说完，就已经会被派发成新任务。要是同一轮里有多个 tool，它们会并行执行。细节见 [impl-notes/stream-parser](../impl-notes/stream-parser.md)。
2. **同一时间只会有一轮 LLM。** 每个 creature 都有一把锁，保证 controller 不会被重入。trigger 可以随便触发，但都得排队。
3. **direct、background、stateful** 只是派发模式，不是三套完全不同的系统。见 [modules/tool](../modules/tool.md)。

## 其他模块放在哪

- **Input** 负责往队列里推事件，除此之外没什么特别的。
- **Triggers** 各自持有一个后台任务，条件满足时就往队列里塞事件。
- **Tools 和 sub-agents** 通过 executor / sub-agent manager 运行。它们完成后会重新变成新事件，整个循环就闭合了。
- **Output** 消费 controller 产生的文本流和 tool 活动流，再把它们发到一个或多个目标上，比如 stdout、TTS、Discord，或者你自己配置的别的地方。

## concept 文档在这一层讲什么，不讲什么

这一页是架构总览。每个模块更细的内容，都放在各自那篇文档里：

- [Controller](../modules/controller.md) —— 循环本身
- [Input](../modules/input.md) —— 第一种 trigger
- [Trigger](../modules/trigger.md) —— 世界怎么把 agent 唤醒
- [Output](../modules/output.md) —— agent 怎么把东西送回外部世界
- [Tool](../modules/tool.md) —— agent 的手
- [Sub-agent](../modules/sub-agent.md) —— 受上下文范围约束的委托者

还有两块是横切的，不适合压在某一个模块上讲，所以单列出来：

- [Channel](../modules/channel.md) —— tools、triggers 和 terrariums 共享的通信底层。
- [Session and environment](../modules/session-and-environment.md) —— 私有状态和共享状态怎么分开。

## 另见

- [Agent as a Python object](../python-native/agent-as-python-object.md) —— 如果你把它嵌进普通 Python 里，这张图会怎么对应过去。
- [impl-notes/stream-parser](../impl-notes/stream-parser.md) —— 为什么 tool 会在 LLM 还没停下时就先启动。
- [impl-notes/prompt-aggregation](../impl-notes/prompt-aggregation.md) —— 驱动这套循环的 system prompt 是怎么拼出来的。