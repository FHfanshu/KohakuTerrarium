# 组合 agent

[什么是 agent](/concepts/foundations/what-is-an-agent.md)（英文）介绍了六个模块。这一页说的是，它们在一个正在运行的 creature 里怎么拼到一起。

## 统一的封装：`TriggerEvent`

控制器外部的一切，都会以 `TriggerEvent` 的形式进入系统：

- 用户输入内容 → `TriggerEvent(type="user_input", content=...)`
- 定时器触发 → `TriggerEvent(type="timer", ...)`
- 工具执行完成 → `TriggerEvent(type="tool_complete", job_id=..., content=...)`
- 子 agent 返回结果 → `TriggerEvent(type="subagent_output", ...)`
- channel 消息 → `TriggerEvent(type="channel_message", ...)`
- 上下文注入 → `TriggerEvent(type="context_update", ...)`
- 错误 → `TriggerEvent(type="error", stackable=False, ...)`

所有东西都进同一种封装。控制器不用为每个来源走不同代码路径；它只需要问一句：这一轮我拿到了哪些事件？架构上的简化，核心就在这。

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

所有唤醒源都会把事件推到同一个队列里。多个“同时”到达的事件如果是 **stackable**，控制器会把它们合并进同一轮用户消息里。这样一阵密集活动，不会变成一阵密集的 LLM 调用。

不能堆叠的事件，比如错误或高优先级信号，会打断这次批处理。它们会单独占一轮。

## 一轮是怎么跑的

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

有几个不变条件值得注意：

1. **工具会立刻启动。** 工具块一解析完，就会被派发成新任务，不用等 LLM 说完。哪怕它还在持续输出，也不影响。一个回合里多个工具会并行运行。细节见 [impl-notes/stream-parser](/concepts/impl-notes/stream-parser.md)（英文）。
2. **同一时间只会有一轮 LLM turn。** 每个 creature 都有一把锁，保证控制器不会被重入。trigger 可以随便触发，但都会先进队列。
3. **direct、background、stateful 是派发模式，不是三套独立系统。** 见 [modules/tool](/concepts/modules/tool.md)（英文）。

## 其他模块放在哪里

- **Input** 负责把事件推入队列，除此之外它本身不变。
- **Triggers** 各自拥有后台任务；条件满足时，就把事件推入队列。
- **Tools 和 sub-agents** 通过 executor / sub-agent manager 运行。它们完成后会变成新的事件，整个环就闭合了。
- **Output** 消费控制器产出的文本和工具活动流，再把它们路由到一个或多个输出端，比如 stdout、TTS、Discord，或者你配置的其他目标。

## 这一层的概念文档讲什么，不讲什么

这一页给的是架构总览。每个模块更细的内容，都在各自的模块文档里：

- [Controller](/concepts/modules/controller.md)（英文）— 循环本身
- [Input](/concepts/modules/input.md)（英文）— 第一个 trigger
- [Trigger](/concepts/modules/trigger.md)（英文）— 从外部世界唤醒 agent
- [Output](/concepts/modules/output.md)（英文）— agent 到外部世界
- [Tool](/concepts/modules/tool.md)（英文）— agent 的手
- [Sub-agent](/concepts/modules/sub-agent.md)（英文）— 带上下文边界的委托者

还有两个横切部分，不适合挂在某一个模块下面，所以单独成节：

- [Channel](/concepts/modules/channel.md)（英文）— tools、triggers 和 terrariums 共享的通信底层。
- [Session and environment](/concepts/modules/session-and-environment.md)（英文）— 私有状态和共享状态怎么划分。

## 另见

- [Agent as a Python object](/concepts/python-native/agent-as-python-object.md)（英文）— 把它嵌进普通 Python 时，这套结构怎么对应过去。
- [impl-notes/stream-parser](/concepts/impl-notes/stream-parser.md)（英文）— 为什么工具会在 LLM 停止输出前启动。
- [impl-notes/prompt-aggregation](/concepts/impl-notes/prompt-aggregation.md)（英文）— 驱动这个循环的 system prompt 是怎么构造出来的。
