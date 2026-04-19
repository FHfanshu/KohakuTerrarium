# 框架内部实现

这篇就是运行时地图。建议你一边看，一边开着 `src/kohakuterrarium/` 对代码。`../concepts/` 下面那些文档讲的是为什么这么设计，这篇只讲东西放哪、流程怎么跑。公开的 Python API 签名在 `plans/inventory-python-api.md`。

这里一共整理了 16 条流程，分三组：

1. **Agent runtime** — 生命周期、controller 循环、tool pipeline、sub-agent、trigger、prompt 聚合、plugin。
2. **Persistence & memory** — session 持久化、压缩。
3. **Multi-agent & serving** — terrarium runtime、channel、environment 和 session 的区别、serving 层、compose 代数、package 系统、MCP。

最后还有一节 [跨流程不变量](#跨流程不变量)，专门放那些全系统都得守的硬规则。

---

## 1. Agent runtime

### 1.1 Agent 生命周期（独立 creature）

CLI 入口在 `cli/run.py:run_agent_cli()`。它会先检查配置路径，再选 I/O 模式（`cli` / `plain` / TUI），按需要创建 `SessionStore`，然后调 `Agent.from_path(config_path, …)`，最后走 `_run_agent_rich_cli()` 或 `agent.run()`。

`Agent.__init__`（`src/kohakuterrarium/core/agent.py:146`）会按固定顺序做初始化：`_init_llm`、`_init_registry`、`_init_executor`、`_init_subagents`、`_init_output`、`_init_controller`、`_init_input`、`_init_user_commands`、`_init_triggers`。mixin 布局是 `AgentInitMixin`（`bootstrap/agent_init.py`）+ `AgentHandlersMixin`（`core/agent_handlers.py`）+ `AgentToolsMixin`（`core/agent_tools.py`）。

`await agent.start()`（`core/agent.py:186`）会把 input 和 output 模块拉起来；如果有 TUI，就把回调挂上；再启动 trigger manager、接 completion callback、初始化 MCP、把 tool 描述注入 prompt、初始化 `CompactManager`、加载 plugin、发布 session 信息，最后启动 termination checker。

`await agent.run()`（`core/agent.py:684`）在恢复 session 时，会先重放 session event、恢复 triggers、触发 startup trigger，然后进入主循环：
`event = await input.get_input()` → `_process_event(event)`。`stop()` 会按相反顺序把这些东西拆掉。agent 自己手里一直持有这些对象：`llm`、`registry`、`executor`、`session`、`environment`、`subagent_manager`、`output_router`、`controller`、`input`、`trigger_manager`、`compact_manager`、`plugins`。

概念层说明见 [concepts/foundations/composing-an-agent.md](../concepts/foundations/composing-an-agent.md)。API 签名见 `plans/inventory-python-api.md` 里的 §Core Agent Lifecycle。

### 1.2 Controller 循环和事件模型

所有东西最后都会变成 `TriggerEvent`（`core/events.py`）。字段有：
`type, content, context, timestamp, job_id?, prompt_override?, stackable`。
类型包括 `user_input`、`idle`、`timer`、`context_update`、`tool_complete`、`subagent_output`、`channel_message`、`monitor`、`error`、`startup`、`shutdown`。

事件队列在 `core/controller.py:push_event` / `_collect_events`（252-299 行）。同一个 tick 里收集到的 stackable event，会并成这一轮里的同一条 user message；非 stackable event 会直接打断当前 batch；超过当前 batch 的事件会先塞进 `_pending_events`，下一轮再处理。

每一轮的流程在 `agent_handlers.py:_run_controller_loop`：

1. 收集事件，拼出这轮上下文。
2. 构造 messages，然后开始从 LLM 流式读取。
3. 一边读，一边解析 tool / sub-agent / command event。
4. 每解析到一个，就立刻用 `asyncio.create_task` 分发出去。也就是说 tool 是在流式输出过程中启动的，不是等 LLM 全说完才开跑。
5. 流结束后，对 direct 模式的完成项做 `asyncio.gather`。
6. 推入合并后的反馈事件，再决定要不要继续下一轮。

相关文档见 [concepts/modules/controller.md](../concepts/modules/controller.md) 和 [stream-parser 实现说明](../concepts/impl-notes/stream-parser.md)。

### 1.3 Tool 执行流水线

stream parser（`parsing/`）在识别到配置好的 `tool_format` 里的 tool block 时，会发事件。支持 bracket（默认：`[/bash]@@command=ls\n[bash/]`）、XML（`<bash command="ls"></bash>`）和 native（LLM provider 自带的 function-calling 封装）。每个识别出来的 tool，都会经由 `executor.submit_from_event()` 变成一个 executor task。

executor（`core/executor.py`）会维护 `{job_id: asyncio.Task}`，每次调用都会建一个 `ToolContext`。里面会带 `working_dir`、`session`、`environment`、文件保护设置、文件读取状态 map、job store，还有 agent 名字。

一共三种模式：

- **Direct** — 当前轮就等它跑完，结果会并进下一次 controller feedback event。
- **Background** — 如果 tool 结果里有 `run_in_background=true`，任务就继续在后台跑；跑完再发未来的 `tool_complete` event。
- **Stateful** — 像 sub-agent 这种长生命周期 handle。结果会存进 `jobs`，之后通过框架命令 `wait` 取回。

这里有几条硬规则，`agent_handlers.py` 和 `executor.py` 都在守：

- tool block 一识别出来就得立刻启动，不能等到 LLM 停下再统一排队。
- 同一轮里的多个 tool 要并行跑，靠 `asyncio.gather`。
- tool 执行不能把 LLM 的流式输出卡住。

更多内容见 [concepts/modules/tool.md](../concepts/modules/tool.md) 和 [impl-notes/stream-parser.md](../concepts/impl-notes/stream-parser.md)。API 参考在 `plans/inventory-python-api.md` 的 §Tool Execution。

### 1.4 Sub-agent 分发

Sub-agent 由 `modules/subagent/manager.py:spawn` 拉起来。深度受 `config.max_subagent_depth` 限制。新的 `SubAgent`（`modules/subagent/base.py`）会复用父级的 registry、LLM 和 tool format，但自己有独立对话。

执行完以后，它会把一个 `subagent_output` event 推回父 controller。如果这个 sub-agent 配了 `output_to: external`，输出就直接流到某个具名 output module，不再回父级。

交互式 sub-agent（`modules/subagent/interactive.py` + `interactive_mgr.py`）会跨多轮一直活着，能吃 `context_update`，也能通过 `_feed_interactive()` 接新 prompt。它们和顶层对话一样，也会持久化进 session store。

相关文档见 [concepts/modules/sub-agent.md](../concepts/modules/sub-agent.md)。

### 1.5 Trigger 系统

`modules/trigger/base.py` 定义了 `BaseTrigger`：一个会 yield `TriggerEvent` 的 async generator。`to_resume_dict()` / `from_resume_dict()` 负责持久化。

内建 trigger 有 `TimerTrigger`、`IdleTrigger`、`ChannelTrigger`、`HTTPTrigger`，还有 monitor 相关 trigger。`TriggerManager`（`core/trigger_manager.py`）会维护 trigger 字典和对应后台 task。启动时，它会给每个 trigger 拉一个 task，不断迭代 `fire()`，把事件推进 agent 队列。`CallableTriggerTool`（`modules/trigger/callable.py`）会把通用 trigger 类包起来，这样 agent 就能在运行时热插 trigger。

恢复 session 时，trigger 状态会从 session store 里的 `events[agent]:*` 记录重建出来。

相关文档见 [concepts/modules/trigger.md](../concepts/modules/trigger.md)。

### 1.6 Prompt 聚合

`prompt/aggregator.py:aggregate_system_prompt` 会按这个顺序组最终的 system prompt：

1. 基础 prompt，也就是 `system.md` 里的 agent personality。它会经由 Jinja2 和 `render_template_safe` 渲染，所以没定义的变量会变成空字符串。
2. Tool 文档。`skill_mode: dynamic` 时这里只放名字和一行说明；`static` 时会塞完整文档。
3. Channel topology 提示，由 `terrarium/config.py:build_channel_topology_prompt` 在 creature 构建时生成。
4. 各种 tool format 对应的框架提示（bracket / xml / native）。
5. Named-output 说明，也就是怎么往 `discord`、`tts` 这种输出写内容。

这些部分会用双换行拼起来。`system.md` 里**不要自己写** tool 列表、tool call 语法或完整 tool 文档。这些内容要么框架自动拼，要么通过框架命令 `info` 按需拿。

相关文档见 [impl-notes/prompt-aggregation.md](../concepts/impl-notes/prompt-aggregation.md)。

### 1.7 Plugin 系统

这里其实是两套互相分开的系统。

**Prompt plugin**（`prompt/plugins.py`）会在聚合 system prompt 时往里加内容。它们按 priority 排序。内建的有 `ToolList`、`FrameworkHints`、`EnvInfo`、`ProjectInstructions`。

**Lifecycle plugin**（`bootstrap/plugins.py`，管理器在 `modules/plugin/`）会挂到 agent event 上。`PluginManager.notify(hook, **kwargs)` 会等所有启用 plugin 的匹配方法跑完。要是某个 `pre_*` hook 抛了 `PluginBlockError`，当前操作就会被拦下来。可用 hook 列表在 builtin inventory 里。

Package 可以在 `kohaku.yaml` 里声明 plugin；`config.plugins[]` 里列出的 plugin 会在 agent 启动时加载。

相关文档见 [concepts/modules/plugin.md](../concepts/modules/plugin.md)。

---

## 2. Persistence & memory

### 2.1 Session 持久化

Session 都存在单个 `.kohakutr` 文件里，底层是 KohakuVault（SQLite）。`session/store.py` 里定义的表有：`meta`、`state`、`events`（append-only）、`channels`（消息历史）、`subagents`（销毁前快照）、`jobs`、`conversation`（每个 agent 最新快照）、`fts`（全文索引）。

写入发生在这些时候：

- 每次 tool 调用、文本 chunk、trigger 触发、token usage 发出时（event log）
- 每轮结束时（conversation snapshot）
- scratchpad 写入时
- channel 发送时

恢复逻辑在 `session/resume.py`：先加载 `meta`，再加载每个 agent 的 conversation snapshot，恢复 scratchpad/state，恢复 trigger，把 event 重放给 output module（为了 scrollback），再把 sub-agent 对话挂回去。不能恢复的状态，比如打开着的文件、LLM 连接、TUI、asyncio task，都会按配置重新建。

`session/memory.py` 和 `session/embedding.py` 提供基于 event log 的 FTS5 和向量搜索。embedding provider 支持 `model2vec`、`sentence-transformer`、`api`。向量会和 event block 一起存，用于混合搜索。

相关文档见 [impl-notes/session-persistence.md](../concepts/impl-notes/session-persistence.md)。

### 2.2 上下文压缩

`core/compact.py:CompactManager` 每轮结束后都会跑。`should_compact(prompt_tokens)` 会检查 prompt token 是否超过 `max_context` 的 80%（可以用 `compact.threshold` 和 `compact.max_tokens` 调）。触发后，它会先发一个 `compact_start` activity event，再起后台 task 去跑 summarizer LLM。默认用主 LLM，也可以单独配 `compact_model`。summary 会在**轮与轮之间**原子性地插进对话。live zone，也就是最近 `keep_recent_turns` 轮，永远不会被总结。

这么做就能保证 controller 不会在一轮跑到一半时，突然发现前面的消息没了。完整原因见 [impl-notes/non-blocking-compaction.md](../concepts/impl-notes/non-blocking-compaction.md)。

---

## 3. Multi-agent & serving

### 3.1 Terrarium runtime

`terrarium/runtime.py:TerrariumRuntime.start`（85-180 行）会先预创建共享 channel，保证每个 creature 都有自己的 direct queue；如果有 root，还会多一个 `report_to_root`；然后通过 `terrarium/factory.py:build_creature` 构建并启动每个 creature，最后再构建 root（这时候还没启动），接着启动 termination checker。

`build_creature` 会通过 `@pkg/...` 或路径加载基础配置，创建 `Agent(session=Session(creature_name), environment=shared_env, …)`，给每个 listen-channel 注册 `ChannelTrigger`，再把 channel topology prompt 拼到 system prompt 后面。creature 不会直接知道自己在 terrarium 里，它只能通过 channel 和可选的 topology hint 间接感知。

root agent 的 environment 上会挂一个 `TerrariumToolManager`，这样它就能用 `terrarium_*` 和 `creature_*` tools。root 永远在系统外侧，不是 peer。

`terrarium/hotplug.py:HotPlugMixin` 提供运行时的 `add_creature`、`remove_creature`、`add_channel`、`remove_channel`。`terrarium/observer.py:ChannelObserver` 会在 channel send 上挂无破坏性的 callback，这样 dashboard 就能观察 queue channel，但不会把消息吃掉。

相关文档见 [concepts/multi-agent/terrarium.md](../concepts/multi-agent/terrarium.md) 和 [concepts/multi-agent/root-agent.md](../concepts/multi-agent/root-agent.md)。

### 3.2 Channels

`core/channel.py` 定义了两个基础类型：

- `SubAgentChannel` — 队列型，一个消息只给一个 consumer，FIFO。支持 `send` / `receive` / `try_receive`。
- `AgentChannel` — 广播型。每个订阅者都会通过 `ChannelSubscription` 拿到自己的队列。晚订阅的人收不到历史消息。

Channel 都放在 `ChannelRegistry` 里，要么挂在 `environment.shared_channels` 下（整个 terrarium 共用），要么挂在 `session.channels` 下（单个 creature 私有）。自动创建的 channel 包括每个 creature 自己的队列，以及 `report_to_root`。`ChannelTrigger` 会把某个 channel 绑到 agent 的事件流上，把收到的消息转成 `channel_message` event。

相关文档见 [concepts/modules/channel.md](../concepts/modules/channel.md)。

### 3.3 Environment 和 Session 的区别

- `Environment`（`core/environment.py`）放整个 terrarium 级别的状态：`shared_channels`、可选的共享 context dict、session bookkeeping。
- `Session`（`core/session.py`）放单个 creature 的状态：私有 channel registry（也可能直接别名到 environment 的）、`scratchpad`、`tui` 引用、`extra` dict。

每个 agent 实例都有一个 session。到了 terrarium 里，environment 是所有 creature 共用的，session 则各管各的。creature 之间不能直接碰彼此的 session。共享状态只能走 `environment.shared_channels`，别偷偷绕过去。

相关文档见 [concepts/modules/session-and-environment.md](../concepts/modules/session-and-environment.md)。

### 3.4 Serving 层

`serving/manager.py:KohakuManager` 会给传输层代码创建 `AgentSession` 或 `TerrariumSession` 这种包装。
`AgentSession.send_input` 会把 user-input event 推进 agent，然后把 output-router event 变成 JSON dict 往外吐：`text`、`tool_start`、`tool_complete`、`activity`、`token_usage`、`compact_*`、`job_update` 等。

`api/` 里的 HTTP/WS API，还有所有 Python embedding，走的都是这一层，不会直接去碰 `Agent` 内部。

API 签名见 `plans/inventory-python-api.md` 的 §Serving。

### 3.5 Compose 代数内部实现

`compose/core.py` 定义了 `BaseRunnable.run(input)` 和 `__call__(input)`。运算符重载会把组合关系包起来：

- `__rshift__`（`>>`）→ `Sequence`；如果右边是 dict，会变成 `Router`。
- `__and__`（`&`）→ `Product`（并行跑）。
- `__or__`（`|`）→ `Fallback`。
- `__mul__`（`*`）→ `Retry`。

普通 callable 会自动包成 `Pure`。`agent()` 会创建持久化的 `AgentRunnable`（多次调用共享对话）；`factory()` 会创建 `AgentFactory`，每次调用都新建一个 agent。`iterate(async_iter)` 会遍历异步数据源，并对每个元素等整条 pipeline 跑完。`effects.Effects()` 用来记录挂在 pipeline 上的副作用，可通过 `pipeline.effects.get_all()` 读取。

相关文档见 [concepts/python-native/composition-algebra.md](../concepts/python-native/composition-algebra.md)。

### 3.6 Package / extension 系统

安装入口是 `packages.py:install_package(source, editable=False)`。支持三种模式：git clone、本地复制，或者 editable 模式下用 `.link` 指针。落地目录是 `~/.kohakuterrarium/packages/<name>/`。

路径解析靠 `resolve_package_path("@<pkg>/<sub>")`。它会顺着 `.link` 走，或者直接遍历目录。配置加载器，比如 `base_config: "@pkg/creatures/..."`，还有 CLI 命令，都靠它找路径。

`kohaku.yaml` manifest 里会声明 package 里的 `creatures`、`terrariums`、`tools`、`plugins`、`llm_presets`、`python_dependencies`。

这几个词别混：

- **Extension** — package 提供的 Python 模块，比如 tool、plugin、LLM preset。
- **Plugin** — 实现生命周期 hook 的那类东西。
- **Package** — 可安装单位，可以包含前两者，也可以只带配置。

### 3.7 MCP 集成

`mcp/client.py:MCPClientManager.connect(cfg)` 会打开一个 stdio 或 HTTP/SSE session，调用 `session.initialize()`，再用 `list_tools` 找可用工具，并把结果缓存进 `self._servers[name]`。`disconnect(name)` 负责清理。

agent 启动时，MCP 连好后会调 `_inject_mcp_tools_into_prompt()`，生成一个 “Available MCP Tools” 的 markdown 块，把每台 server、每个 tool 和参数集合列出来。agent 调 MCP tool 时，不会直接连 server，而是走内建元工具 `mcp_call(server, tool, args)`。另外还有 `mcp_list`、`mcp_connect`、`mcp_disconnect`。

支持的传输方式有 `stdio`（子进程 stdin/stdout）和 `http/SSE`。

---

## 跨流程不变量

上面这些流程都得守下面这些规则。破一条，系统多半就要出问题。

- **每个 agent 只有一个 `_processing_lock`。** 同一时间只能跑一个 LLM turn。这个约束在 `agent_handlers.py` 里保证。
- **Tool 要并行分发。** 一轮里识别出来的所有 tool 都要一起启动。顺序执行就是 bug。
- **压缩不能阻塞。** 对话替换必须是原子的，而且只能发生在轮与轮之间。controller 不该在一次 LLM 调用半路看到消息消失。
- **事件堆叠规则不能乱。** 一串相同的 stackable event 会并成一条 user message；非 stackable event 一定会打断 batch。
- **要有背压。** `controller.push_event` 在队列满时会等。trigger 暴走时，系统应该限速，不是直接丢事件。
- **Terrarium 的 session 必须隔离。** creature 不能碰彼此的 session。共享状态只走 `environment.shared_channels`，没有例外。

只要你改了这些流程里的任何一段，都该回来再对一遍这些规则。真正的准绳是 inventory（`plans/inventory-runtime.md`），代码改了，它也要跟着更新。

TODO：inventory 现在对 `compose/` 包的细节还没完全覆盖，这里写得比那边细；`commands/` 的 framework-command runtime 也还没完全补进去，output router 的状态机也没补全。等下一轮 inventory 更新时，再把这些补齐。
