# 框架内部结构

按实现层面梳理运行时结构，分成三层。

默认你在读这份文档时，旁边已经打开了 `src/kohakuterrarium/`。`/concepts/` 下的概念文档解释“为什么”，这份文档只说“在哪里”。公开的 Python API 签名见 [`/plans/inventory-python-api.md`](/plans/inventory-python-api.md)（英文）。

下面记了 16 条流程，分三组：

1. **Agent 运行时**：生命周期、controller 循环、工具管线、sub-agent、trigger、prompt 聚合、plugin。
2. **持久化与 memory**：session 持久化、compaction。
3. **多 agent 与 serving**：terrarium 运行时、channel、environment 和 session 的区别、serving 层、compose 代数、package 系统、MCP。

最后的 [跨流程不变量](#跨流程不变量) 汇总了整个系统都要遵守的规则。

---

## 1. Agent 运行时

### 1.1 Agent 生命周期（独立 creature）

CLI 入口是 `cli/run.py:run_agent_cli()`。它会校验配置路径，选择 I/O 模式（`cli` / `plain` / TUI），按需创建 `SessionStore`，然后调用 `Agent.from_path(config_path, …)`，再分派到 `_run_agent_rich_cli()` 或 `agent.run()`。

`Agent.__init__`（`src/kohakuterrarium/core/agent.py:146`）按固定顺序完成启动：`_init_llm`、`_init_registry`、`_init_executor`、`_init_subagents`、`_init_output`、`_init_controller`、`_init_input`、`_init_user_commands`、`_init_triggers`。mixin 结构是 `AgentInitMixin`（`bootstrap/agent_init.py`）+ `AgentHandlersMixin`（`core/agent_handlers.py`）+ `AgentToolsMixin`（`core/agent_tools.py`）。

`await agent.start()`（`core/agent.py:186`）会启动 input 和 output 模块；如果有 TUI，就接好回调；启动 trigger manager；接入 completion 回调；初始化 MCP（连接服务器并把工具说明注入 prompt）；初始化 `CompactManager`；加载 plugin；发布 session 信息；最后启动 termination checker。

`await agent.run()`（`core/agent.py:684`）在恢复 session 时会先重放 session event，恢复 trigger，触发 startup trigger，然后进入循环：`event = await input.get_input()` → `_process_event(event)`。`stop()` 会按相反顺序拆掉这些部分。agent 持有这些对象：`llm`、`registry`、`executor`、`session`、`environment`、`subagent_manager`、`output_router`、`controller`、`input`、`trigger_manager`、`compact_manager`、`plugins`。

概念图见 [`/concepts/foundations/composing-an-agent.md`](/concepts/foundations/composing-an-agent.md)（英文）。API 签名见 `plans/inventory-python-api.md` 的 §Core Agent Lifecycle。

### 1.2 Controller 循环和事件模型

一切都通过 `TriggerEvent`（`core/events.py`）流动。字段有：`type`、`content`、`context`、`timestamp`、`job_id?`、`prompt_override?`、`stackable`。类型包括 `user_input`、`idle`、`timer`、`context_update`、`tool_complete`、`subagent_output`、`channel_message`、`monitor`、`error`、`startup`、`shutdown`。

事件队列在 `core/controller.py:push_event` / `_collect_events`（252-299 行）。同一个 tick 里收集到的可堆叠事件会合并成当前轮的一条用户消息；不可堆叠事件会切断这一批；超出当前批次的事件会存进 `_pending_events`，留到下一轮处理。

每轮流程在 `agent_handlers.py:_run_controller_loop`：

1. 收集事件，形成一轮的上下文。
2. 构造消息，从 LLM 流式读取输出。
3. 在流里边读边解析 tool / sub-agent / command 事件。
4. 每个事件都用 `asyncio.create_task` 分派出去（工具在流式输出期间就会启动，不会等流结束）。
5. 流结束后，对 direct 模式的完成任务执行 `asyncio.gather`。
6. 推入合并后的反馈事件，再决定要不要继续下一轮。

见 [`/concepts/modules/controller.md`](/concepts/modules/controller.md)（英文）和 [`/concepts/impl-notes/stream-parser.md`](/concepts/impl-notes/stream-parser.md)（英文）。

### 1.3 工具执行管线

流解析器（`parsing/`）在检测到配置的 `tool_format` 里的工具块时会发出事件——可以是 bracket（默认：`[/bash]@@command=ls\n[bash/]`）、XML（`<bash command="ls"></bash>`），也可以是 native（LLM 提供商自己的 function-calling 封装）。每个识别出的工具都会通过 `executor.submit_from_event()` 变成一个 executor task。

executor（`core/executor.py`）会保存 `{job_id: asyncio.Task}`，并为每次调用构造一个 `ToolContext`，里面有 `working_dir`、`session`、`environment`、文件保护规则、文件读取状态表、job 存储和 agent 名称。

有三种模式：

- **Direct**：在当前轮里等待完成，结果会汇总进下一次 controller feedback event。
- **Background**：工具结果里带 `run_in_background=true`。任务继续跑，完成后再发一个未来的 `tool_complete` 事件。
- **Stateful**：sub-agent 这类长生命周期句柄。结果存进 `jobs`，通过 `wait` 框架命令取回。

不变量（在 `agent_handlers.py` 和 `executor.py` 里保证）：

- 工具块一解析出来就启动，不会等 LLM 先把话说完。
- 同一轮里的多个工具并行运行（`asyncio.gather`）。
- LLM 的流式输出不会被工具执行卡住。

见 [`/concepts/modules/tool.md`](/concepts/modules/tool.md)（英文）和 [`/concepts/impl-notes/stream-parser.md`](/concepts/impl-notes/stream-parser.md)（英文）。API 见 `plans/inventory-python-api.md` 的 §Tool Execution。

### 1.4 Sub-agent 分派

Sub-agent 由 `modules/subagent/manager.py:spawn` 启动。深度受 `config.max_subagent_depth` 限制。新的 `SubAgent`（`modules/subagent/base.py`）复用父级的 registry、LLM 和 tool format，但维护自己的对话。

完成后会把一个 `subagent_output` 事件推回父 controller。如果 sub-agent 配置了 `output_to: external`，它的输出会直接流到指定的 output 模块，而不是先回父级。

交互式 sub-agent（`modules/subagent/interactive.py` + `interactive_mgr.py`）会跨多轮存活，接收上下文更新，也能通过 `_feed_interactive()` 喂入新 prompt。它们和顶层对话一样，会持久化到 session store。

见 [`/concepts/modules/sub-agent.md`](/concepts/modules/sub-agent.md)（英文）。

### 1.5 Trigger 系统

`modules/trigger/base.py` 定义了 `BaseTrigger`：一个会产出 `TriggerEvent` 的异步生成器。`to_resume_dict()` / `from_resume_dict()` 负责持久化。

内置 trigger 有 `TimerTrigger`、`IdleTrigger`、`ChannelTrigger`、`HTTPTrigger` 和 monitor trigger。`TriggerManager`（`core/trigger_manager.py`）维护 trigger 字典和对应的后台任务。启动时，它会给每个 trigger 启一个任务，迭代 `fire()`，再把事件推入 agent 的队列。`CallableTriggerTool`（`modules/trigger/callable.py`）把每个通用 trigger 类封装起来，让 agent 能在运行时热插 trigger。

恢复 session 时，trigger 状态会从 session store 里的 `events[agent]:*` 记录重建。

见 [`/concepts/modules/trigger.md`](/concepts/modules/trigger.md)（英文）。

### 1.6 Prompt 聚合

`prompt/aggregator.py:aggregate_system_prompt` 按这个顺序组装最终的 system prompt：

1. 基础 prompt（来自 `system.md` 的 agent personality），通过 Jinja2 和 `render_template_safe` 渲染，未定义变量会退化为空字符串。
2. 工具文档。`skill_mode: dynamic` 时只放名称加一行描述；`static` 时放完整文档。
3. channel 拓扑提示，由 `terrarium/config.py:build_channel_topology_prompt` 在构建 creature 时生成。
4. 按 tool format 加的框架提示（bracket / xml / native）。
5. 命名输出模型（如何写到 `discord`、`tts` 等输出）。

各部分用两个换行拼接。`system.md` 里不能包含工具列表、工具调用语法或完整工具文档——这些内容要么自动聚合，要么通过 `info` 框架命令按需加载。

见 [`/concepts/impl-notes/prompt-aggregation.md`](/concepts/impl-notes/prompt-aggregation.md)（英文）。

### 1.7 Plugin 系统

这是两套互相独立的系统：

**Prompt plugin**（`prompt/plugins.py`）在聚合阶段往 system prompt 里插内容，按优先级排序。内置项包括 `ToolList`、`FrameworkHints`、`EnvInfo`、`ProjectInstructions`。

**Lifecycle plugin**（`bootstrap/plugins.py` 和 `modules/plugin/` 里的 manager）挂在 agent event 上。`PluginManager.notify(hook, **kwargs)` 会等待每个启用 plugin 上对应的方法执行完。`pre_*` hook 如果抛出 `PluginBlockError`，当前操作就会中止。可用 hook 列在 builtin inventory 里。

Package 在 `kohaku.yaml` 里声明 plugin；`config.plugins[]` 里列出的 plugin 会在 agent 启动时加载。

见 [`/concepts/modules/plugin.md`](/concepts/modules/plugin.md)（英文）。

---

## 2. 持久化与 memory

### 2.1 Session 持久化

Session 保存在单个 `.kohakutr` 文件里，底层是 KohakuVault（SQLite）。`session/store.py` 里的表包括：`meta`、`state`、`events`（只追加）、`channels`（消息历史）、`subagents`（销毁前快照）、`jobs`、`conversation`（每个 agent 的最新快照）、`fts`（全文索引）。

会在这些时机写入：

- 每次 tool call、文本 chunk、trigger 触发和 token usage 发出时（event log）；
- 每轮结束时（conversation snapshot）；
- scratchpad 写入时；
- channel 发送时。

恢复流程见 `session/resume.py`：加载 `meta`，加载每个 agent 的 conversation snapshot，恢复 scratchpad/state，恢复 trigger，把 event 重放给 output 模块（用于 scrollback），重新挂回 sub-agent 对话。不能恢复的状态——比如打开的文件、LLM 连接、TUI、`asyncio` task——会按配置重新创建。

`session/memory.py` 和 `session/embedding.py` 基于 event log 提供 FTS5 和向量搜索。embedding provider 有 `model2vec`、`sentence-transformer`、`api`。向量和 event block 一起存，用于混合检索。

见 [`/concepts/impl-notes/session-persistence.md`](/concepts/impl-notes/session-persistence.md)（英文）。

### 2.2 上下文压缩

`core/compact.py:CompactManager` 每轮结束后运行。`should_compact(prompt_tokens)` 会检查 prompt token 是否超过 `max_context` 的 80%（可通过 `compact.threshold` 和 `compact.max_tokens` 配置）。触发后，它会发出一个 `compact_start` activity event，启动后台任务调用 summarizer LLM（默认是主 LLM；如果配了 `compact_model`，就用单独模型），并在**轮与轮之间**以原子方式把摘要插进对话。实时区——最近的 `keep_recent_turns` 轮——永远不会被摘要化。

这种原子插入设计保证 controller 不会在一轮进行到一半时看到消息突然消失。完整原因见 [`/concepts/impl-notes/non-blocking-compaction.md`](/concepts/impl-notes/non-blocking-compaction.md)（英文）。

---

## 3. 多 agent 与 serving

### 3.1 Terrarium 运行时

`terrarium/runtime.py:TerrariumRuntime.start`（85-180 行）会先创建共享 channel，确保每个 creature 都有 direct-queue；如果有 root，就加上 `report_to_root`；然后通过 `terrarium/factory.py:build_creature` 构建每个 creature，启动这些 creature，最后再构建 root（此时还不启动），然后启动 termination checker。

`build_creature` 会通过 `@pkg/...` 或路径加载基础配置，创建 `Agent(session=Session(creature_name), environment=shared_env, …)`，为每个监听 channel 注册一个 `ChannelTrigger`，再把 channel 拓扑提示拼到 system prompt 后面。creature 不会知道自己身处 terrarium，除非通过它的 channel，或者显式开启了 topology hint。

root agent 的 environment 上会挂一个 `TerrariumToolManager`，这样它就能使用 `terrarium_*` 和 `creature_*` 工具。root 始终在外部，不是普通 peer。

`terrarium/hotplug.py:HotPlugMixin` 提供运行时的 `add_creature`、`remove_creature`、`add_channel`、`remove_channel`。`terrarium/observer.py:ChannelObserver` 会在 channel send 上挂非破坏性回调，这样 dashboard 可以观察 queue channel，又不会把消息消费掉。

见 [`/concepts/multi-agent/terrarium.md`](/concepts/multi-agent/terrarium.md)（英文）和 [`/concepts/multi-agent/root-agent.md`](/concepts/multi-agent/root-agent.md)（英文）。

### 3.2 Channel

`core/channel.py` 定义了两个基础类型：

- `SubAgentChannel`：基于队列，每条消息只给一个消费者，FIFO。支持 `send` / `receive` / `try_receive`。
- `AgentChannel`：广播式。每个订阅者通过 `ChannelSubscription` 持有自己的队列。晚加入的订阅者收不到旧消息。

Channel 放在 `ChannelRegistry` 里，位置要么是 `environment.shared_channels`（整个 terrarium 共享），要么是 `session.channels`（creature 私有）。自动创建的 channel 包括每个 creature 自己的队列和 `report_to_root`。`ChannelTrigger` 把 channel 绑定到 agent 的事件流上，把收到的消息转成 `channel_message` 事件。

见 [`/concepts/modules/channel.md`](/concepts/modules/channel.md)（英文）。

### 3.3 Environment 和 Session

- `Environment`（`core/environment.py`）保存 terrarium 范围的状态：`shared_channels`、可选的共享 context dict、session bookkeeping。
- `Session`（`core/session.py`）保存每个 creature 私有的状态：私有 channel registry（或者引用 environment 里的那份）、`scratchpad`、`tui` 引用、`extra` dict。

每个 agent 实例有一个 session。放进 terrarium 后，environment 由所有 creature 共享，session 则各自独立。creature 不会直接碰别人的 session；共享状态只能走 `environment.shared_channels`。

见 [`/concepts/modules/session-and-environment.md`](/concepts/modules/session-and-environment.md)（英文）。

### 3.4 Serving 层

`serving/manager.py:KohakuManager` 会给传输层创建 `AgentSession` 或 `TerrariumSession` 包装。`AgentSession.send_input` 把 user-input event 推进 agent，并把 output-router event 作为 JSON dict 产出：`text`、`tool_start`、`tool_complete`、`activity`、`token_usage`、`compact_*`、`job_update` 等。

`api/` 里的 HTTP/WS API，以及任何 Python 嵌入代码，都通过这一层工作，而不是直接碰 `Agent` 内部实现。

API 签名见 `plans/inventory-python-api.md` 的 §Serving。

### 3.5 Compose 代数内部实现

`compose/core.py` 定义了 `BaseRunnable.run(input)` 和 `__call__(input)`。运算符重载用来包装组合逻辑：

- `__rshift__`（`>>`）→ `Sequence`；如果右侧是 dict，`>>` 会变成 `Router`。
- `__and__`（`&`）→ `Product`（并行运行）。
- `__or__`（`|`）→ `Fallback`。
- `__mul__`（`*`）→ `Retry`。

普通 callable 会自动包成 `Pure`。`agent()` 构造一个持久化的 `AgentRunnable`（多次调用共享同一段对话）；`factory()` 构造 `AgentFactory`，每次调用都创建一个新的 agent。`iterate(async_iter)` 会遍历一个异步源，并对每个元素等待整条 pipeline 跑完。`effects.Effects()` 记录挂在 pipeline 上的 side-effect（通过 `pipeline.effects.get_all()` 读取）。

见 [`/concepts/python-native/composition-algebra.md`](/concepts/python-native/composition-algebra.md)（英文）。

### 3.6 Package / 扩展系统

安装入口：`packages.py:install_package(source, editable=False)`。三种模式：git clone、本地复制，或 editable 模式下的 `.link` 指针。落地目录是 `~/.kohakuterrarium/packages/<name>/`。

解析入口：`resolve_package_path("@<pkg>/<sub>")`。它会跟随 `.link` 指针，或者直接遍历目录。配置加载器（例如 `base_config: "@pkg/creatures/…"`）和 CLI 命令都用它。

`kohaku.yaml` manifest 声明 package 的 `creatures`、`terrariums`、`tools`、`plugins`、`llm_presets` 和 `python_dependencies`。

术语：

- **Extension**：package 提供的 Python 模块（tool / plugin / LLM preset）。
- **Plugin**：实现生命周期 hook 的组件。
- **Package**：可安装单元，可能包含前两者和配置。

### 3.7 MCP 集成

`mcp/client.py:MCPClientManager.connect(cfg)` 会打开 stdio 或 HTTP/SSE 会话，调用 `session.initialize()`，通过 `list_tools` 发现工具，再把结果缓存到 `self._servers[name]`。`disconnect(name)` 负责清理。

agent 启动时，MCP 连接完成后会调用 `_inject_mcp_tools_into_prompt()`，生成一个 “Available MCP Tools” 的 markdown 块，列出每个 server、tool 和参数集合。agent 通过内置的 `mcp_call(server, tool, args)` 元工具调用 MCP 工具，另外还有 `mcp_list`、`mcp_connect`、`mcp_disconnect`。

传输方式有两种：`stdio`（子进程 stdin/stdout）和 `http/SSE`。

---

## 跨流程不变量

下面这些规则贯穿上面的所有流程，破坏任何一条都会出问题。

- **每个 agent 只有一个 `_processing_lock`。** 同一时间只能跑一个 LLM turn。由 `agent_handlers.py` 保证。
- **工具并行分派。** 同一轮里识别出的所有工具一起启动。串行分派就是 bug。
- **非阻塞 compaction。** 对话替换是原子的，而且只发生在轮与轮之间。controller 不会在一次 LLM 调用的中途看到消息消失。
- **事件可堆叠规则。** 一串相同的可堆叠事件会合并成一条用户消息；不可堆叠事件一定会切断批次。
- **背压。** `controller.push_event` 在队列满时会等待。失控的 trigger 会被限速，不会直接丢事件。
- **Terrarium session 隔离。** creature 不会碰彼此的 session。共享状态只走 `environment.shared_channels`，没有例外。

如果你改了任何流程，记得回头检查这些约束。inventory（`plans/inventory-runtime.md`）是事实来源，应该和代码一起更新。

TODO：inventory 目前还没完整覆盖 `compose/` package（这里只写了摘要）、`commands/` 框架命令运行时，以及 output router 状态机。等下一轮 inventory 补齐时，要把这些部分一并展开。
