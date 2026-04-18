# Tool

## 它是什么

**tool** 是 agent 真正去**做事**的方式。它是一项可执行能力，会注册到 controller 上，LLM 可以按名字带参数调用它。

很多人脑子里的 tool 就是“LLM 能调的一个函数”：`bash`、`read`、`write`、`grep`、`web_search`。这当然没错，但也不够。tool 还可以是通往另一个 agent 的消息总线、一个状态机句柄、一个嵌套 creature、一个权限闸门，或者这些东西的混合体。

## 为什么要有它

聊天机器人只有嘴。tool 给 agent 手。没有它，LLM 只能说话；有了它，它才能真的去世界里干活。

这个框架想做的，是让 tool **好用，也好写**：能跟流式输出配合，中途分发，支持并行执行，能传上下文，能跑后台任务，还有带类型的元数据。很多 agent 产品都在重复造这里面的某一部分；把它们收进底层，省得每次重来。

## 怎么定义它

一个 tool 一般会实现这些东西：

- **名字**和简短描述（会自动插进 system prompt）
- **参数 schema**（`parameters`），兼容 JSON Schema
- 异步的 **`execute(args, context) → ToolResult`**
- **执行模式**：`direct`（默认）、`background` 或 `stateful`
- 可选的**完整文档**（`get_full_documentation()`），通过 `info` framework command 按需加载

执行模式分别是：

- **Direct** —— 在当前 turn 内等待 tool 完成，再把结果作为 `tool_complete` 事件喂回去。
- **Background** —— 提交后先放走，结果在之后的事件里回来。
- **Stateful** —— 跨多个 turn 交互；像 generator 一样，会产出中间结果，agent 可以边看边反应。

## 怎么实现它

tool 都注册在 `Registry`（`core/registry.py`）里。controller 的流式解析器一旦看到某个 tool block 闭合，就会立刻调用 `Executor.submit_from_event(...)`。executor 再起一个 `asyncio.Task`，所以多个 tool 可以并行跑。

每次 tool 执行都会拿到一个 `ToolContext`，里面带着：

- creature 的工作目录；
- session（scratchpad、私有 channel）；
- environment（如果有，也就是共享 channel）；
- 文件保护规则（写前先读、路径安全）；
- 文件读取状态（用于去重）；
- agent 名字；
- job store（这样 `wait` / `read_job` framework command 才找得到这个 tool 的 job）。

内置 tool 包括 shell（`bash`）、Python（`python`）、文件操作（`read`、`write`、`edit`、`multi_edit`）、搜索（`glob`、`grep`、`tree`）、JSON（`json_read`、`json_write`）、web（`web_fetch`、`web_search`）、通信（`send_message`）、memory（`scratchpad`、`search_memory`）、自省（`info`、`stop_task`），以及 terrarium 管理（`terrarium_create`、`creature_start` 等）。

## 你能拿它做什么

- **把 tool 当消息总线。** `send_message` 往 channel 写，另一个 creature 上的 `ChannelTrigger` 去读。两个 tool 加一个 trigger，就能拼出群聊模式，不用额外原语。
- **把 tool 当状态句柄。** `scratchpad` 本质上就是个 KV API；几个 cooperating tool 可以在那里会合。
- **让 tool 安装 trigger。** 任意通用 trigger 类（默认有 `TimerTrigger`、`ChannelTrigger`、`SchedulerTrigger`）都可以直接暴露成 tool。只要在 `tools:` 里写 `type: trigger`，`add_timer` / `watch_channel` / `add_schedule` 就会出现在 tool 列表里；调一下就会把 trigger 装到运行中的 `TriggerManager` 上。`terrarium_create` 更是直接起一整套嵌套系统。
- **让 tool 包一层 sub-agent。** sub-agent 调用本来就长得像 tool，因为 LLM 也是按名字加参数去调它。
- **让 tool 里再跑 agent。** tool 是普通 Python，所以一个 tool 里完全可以起个 agent。比如做个 guard tool，先让一个小判断 agent 看参数，再决定要不要放行真正动作。见 [patterns](/zh/concepts/patterns.md)。

## 别把它当铁律

tool 不一定得“纯”。它可以改状态、起长任务、和别的 creature 协作，甚至编排整个 terrarium。它也不一定得直观。一个唯一作用是把 session 标成“可以 compaction 了”的 tool，也完全站得住。抽象层面上它只是“LLM 能调的一样东西”；至于调用之后背后会发生什么，框架并不管太多。

## 另见

- [impl-notes/stream-parser](/zh/concepts/impl-notes/stream-parser.md) —— 为什么 tool 会在 LLM 说完前就启动。
- [Sub-agent](/zh/concepts/modules/sub-agent.md) —— 那个“其实也算 tool”的近亲。
- [Channel](/zh/concepts/modules/channel.md) —— tool 作为消息总线的另一半。
- [Patterns](/zh/concepts/patterns.md) —— 一些不那么直觉的用法。
- [reference/builtins.md — Tools](/zh/reference/builtins.md) —— 完整目录。