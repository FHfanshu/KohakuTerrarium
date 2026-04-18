# 工具

## 它是什么

**工具**是 agent 用来*做事*的方式。它是一种可执行能力，注册到 controller 后，LLM 就能按名字并带参数调用它。

很多人会把工具理解成“LLM 可以调用的函数”：`bash`、`read`、`write`、`grep`、`web_search`。这样说没错，但还不够。工具也可以是通向另一个 agent 的消息总线、状态机句柄、嵌套 creature、权限闸门，或者这些东西的组合。

## 为什么需要它

聊天机器人只有嘴。工具给 agent 加上手。没有工具，LLM 只能说话；有了工具，它就能在外部世界里做各种事。

这个框架要做的，是把工具执行这件事做得既好用，也好写：支持流式分发、并行执行、上下文传递、后台任务和类型化元数据。现在几乎每个 agent 产品都会各自重写其中一部分；把这些能力放进底层，就不用一遍遍重复造轮子。

## 我们怎么定义它

一个工具包括：

- **名称**和简短说明（会自动插入 system prompt）
- **参数模式**（`parameters`），兼容 JSON Schema
- 异步 **`execute(args, context)` → `ToolResult`**
- **执行模式**：`direct`（默认）、`background` 或 `stateful`
- 可选的**完整文档**（`get_full_documentation()`），需要时通过框架命令 `info` 按需加载

执行模式：

- **Direct**：在当前轮次里等待工具执行完成，再把结果作为 `tool_complete` 事件送回去。
- **Background**：提交后立即释放，结果会在后续事件里到达。
- **Stateful**：支持多轮交互；这类工具有点像生成器，会不断产出中间结果，agent 可以据此继续反应。

## 我们怎么实现它

工具注册在 `Registry`（`core/registry.py`）里。controller 的流解析器会在工具块结束时识别出来，并立刻调用 `Executor.submit_from_event(...)`。executor 会创建 `asyncio.Task`，所以多个工具可以并行运行。

每次工具执行都会收到一个 `ToolContext`，里面带着：

- creature 的工作目录
- session（scratchpad、私有通道）
- environment（如果有共享通道）
- 文件保护规则（先读后写、路径安全）
- 文件读取状态（用于去重）
- agent 名称
- job store（这样框架命令 `wait` / `read_job` 才能找到这个工具对应的任务）

内置工具包括 shell（`bash`）、Python（`python`）、文件操作（`read`、`write`、`edit`、`multi_edit`）、搜索（`glob`、`grep`、`tree`）、JSON（`json_read`、`json_write`）、Web（`web_fetch`、`web_search`）、通信（`send_message`）、记忆（`scratchpad`、`search_memory`）、自省（`info`、`stop_task`），以及 terrarium 管理（`terrarium_create`、`creature_start`、……）。

## 因此你可以做什么

- **把工具当消息总线。** `send_message` 会向某个 channel 写消息；另一只 creature 上的 `ChannelTrigger` 会去读。两个工具加一个 trigger，就能做出群聊式模式，不需要额外原语。
- **把工具当状态句柄。** `scratchpad` 是很典型的 KV API；一组互相配合的工具可以通过它会合。
- **让工具安装 trigger。** 任何通用 trigger 类（默认包括 `TimerTrigger`、`ChannelTrigger`、`SchedulerTrigger`）都可以作为工具暴露出来——只要在 `tools:` 下把它列成 `type: trigger`，`add_timer` / `watch_channel` / `add_schedule` 就会出现在工具列表里，调用后会把对应 trigger 安装到运行中的 `TriggerManager`。`terrarium_create` 则会直接启动一整套嵌套系统。
- **让工具包装子 agent。** 任何子 agent 调用本身都长得像工具，因为 LLM 是按名称和参数去调用它的。
- **让工具运行 agent。** 工具本质上就是普通 Python，所以工具内部也可以再放一个 agent。比如做一个 guard 工具，先用一个小型裁决 agent 检查参数，再决定是否转发真实操作。见 [patterns](/concepts/patterns.md)（英文）。

## 不要被边界限制

工具不必是“纯”的。它可以改状态，可以启动长时间任务，可以和别的 creature 协调，也可以编排整个 terrarium。它甚至不一定显眼：一个唯一作用只是把 session 标记为“ready for compaction”的工具，也完全说得通。这里的抽象只是“LLM 可以调用的一样东西”；至于调用之后发生什么，框架不会替你设限。

## 另见

- [impl-notes/stream-parser](/concepts/impl-notes/stream-parser.md)（英文）——为什么工具会在 LLM 停止之前就开始执行。
- [Sub-agent](/concepts/modules/sub-agent.md)（英文）——那个“也算一种工具”的近亲。
- [Channel](/concepts/modules/channel.md)（英文）——“工具作为消息总线”的另一半。
- [Patterns](/concepts/patterns.md)（英文）——工具的一些非常规用法。
- [reference/builtins.md — Tools](/reference/builtins.md)（英文）——完整目录。
