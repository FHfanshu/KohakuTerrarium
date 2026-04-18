# Python API

`kohakuterrarium` Python 包里所有公开的类、函数和协议。条目按模块分组。签名使用现代类型标注。

架构说明见[concepts/README](/concepts/README.md)（英文）。
任务示例见[guides/programmatic-usage](/guides/programmatic-usage.md)（英文）和[guides/custom-modules](/guides/custom-modules.md)（英文）。

## 导入入口

| 当你需要 | 使用 |
|---|---|
| 最省事的流式聊天封装 | `kohakuterrarium.serving.agent_session.AgentSession` |
| 直接控制 agent | `kohakuterrarium.core.agent.Agent` |
| 多 agent 运行时 | `kohakuterrarium.terrarium.runtime.TerrariumRuntime` |
| 与传输层无关的管理器 | `kohakuterrarium.serving.manager.KohakuManager` |
| 加载配置 | `kohakuterrarium.core.config.load_agent_config` / `kohakuterrarium.terrarium.config.load_terrarium_config` |
| 持久化 / 搜索 | `kohakuterrarium.session.store.SessionStore`, `kohakuterrarium.session.memory.SessionMemory` |
| 编写扩展 | `kohakuterrarium.modules.{tool,input,output,trigger,subagent}.base` |
| 组合 pipeline | `kohakuterrarium.compose` |
| 测试 | `kohakuterrarium.testing` |

---

## `kohakuterrarium.core`

### `Agent`

模块：`kohakuterrarium.core.agent`。

主调度器，把 LLM、controller、executor、triggers、I/O 和 plugins 接到一起。继承 `AgentInitMixin`、`AgentHandlersMixin` 和 `AgentMessagesMixin`。

类方法工厂：

```python
Agent.from_path(
    config_path: str,
    *,
    input_module: InputModule | None = None,
    output_module: OutputModule | None = None,
    session: Session | None = None,
    environment: Environment | None = None,
    llm_override: str | None = None,
    pwd: str | None = None,
) -> Agent
```

生命周期：

- `async start() -> None` — 启动 I/O、output、triggers、LLM 和 plugins。
- `async stop() -> None` — 干净地停止所有模块。
- `async run() -> None` — 完整事件循环。若尚未启动，会先调用 `start()`。
- `interrupt() -> None` — 非阻塞；可安全地从任意线程调用。

输入与事件：

- `async inject_input(content: str | list[ContentPart], source: str = "programmatic") -> None`
- `async inject_event(event: TriggerEvent) -> None`

运行时控制：

- `switch_model(profile_name: str) -> str` — 返回解析后的模型 id。
- `async add_trigger(trigger: BaseTrigger, trigger_id: str | None = None) -> str`
- `async remove_trigger(trigger_id_or_trigger: str | BaseTrigger) -> bool`
- `update_system_prompt(content: str, replace: bool = False) -> None`
- `get_system_prompt() -> str`
- `attach_session_store(store: Any) -> None`
- `set_output_handler(handler: Any, replace_default: bool = False) -> None`
- `get_state() -> dict[str, Any]` — name、running、tools、subagents、message count、pending jobs。

属性：

- `is_running: bool`
- `tools: list[str]`
- `subagents: list[str]`
- `conversation_history: list[dict]`

字段：

- `config: AgentConfig`
- `llm: LLMProvider`
- `controller: Controller`
- `executor: Executor`
- `registry: Registry`
- `session: Session`
- `environment: Environment | None`
- `input: InputModule`
- `output_router: OutputRouter`
- `trigger_manager: TriggerManager`
- `session_store: Any`
- `compact_manager: Any`
- `plugins: Any`

说明：

- 多 agent 场景下，`environment` 由 `TerrariumRuntime` 提供；单独运行时为 `None`。
- `Agent` 实例在 `stop()` 之后不能复用；如果要从 `SessionStore` 恢复，重新创建一个。

```python
agent = Agent.from_path("creatures/my_agent", llm_override="claude-opus-4.6")
await agent.start()
await agent.inject_input("Hello")
await agent.stop()
```

### `AgentConfig`

模块：`kohakuterrarium.core.config_types`。数据类。

包含 creature 配置的全部字段。YAML 形式见[configuration.md](/reference/configuration.md)（英文）。

字段：

- `name: str`
- `version: str = "1.0"`
- `base_config: str | None = None`
- `llm_profile: str = ""`
- `model: str = ""`
- `auth_mode: str = ""`
- `api_key_env: str = ""`
- `base_url: str = ""`
- `temperature: float = 0.7`
- `max_tokens: int | None = None`
- `reasoning_effort: str = "medium"`
- `service_tier: str | None = None`
- `extra_body: dict[str, Any]`
- `system_prompt: str = "You are a helpful assistant."`
- `system_prompt_file: str | None = None`
- `prompt_context_files: dict[str, str]`
- `skill_mode: str = "dynamic"`
- `include_tools_in_prompt: bool = True`
- `include_hints_in_prompt: bool = True`
- `max_messages: int = 0`
- `ephemeral: bool = False`
- `input: InputConfig`
- `triggers: list[TriggerConfig]`
- `tools: list[ToolConfigItem]`
- `subagents: list[SubAgentConfigItem]`
- `output: OutputConfig`
- `compact: dict[str, Any] | None = None`
- `startup_trigger: dict[str, Any] | None = None`
- `termination: dict[str, Any] | None = None`
- `max_subagent_depth: int = 3`
- `tool_format: str | dict = "bracket"`
- `agent_path: Path | None = None`
- `session_key: str | None = None`
- `mcp_servers: list[dict[str, Any]]`
- `plugins: list[dict[str, Any]]`

方法：

- `get_api_key() -> str | None` — 读取配置的环境变量。

### `InputConfig`, `OutputConfig`, `OutputConfigItem`, `TriggerConfig`, `ToolConfigItem`, `SubAgentConfigItem`

模块：`kohakuterrarium.core.config_types`。数据类。

**`InputConfig`**

- `type: str = "cli"` — `builtin`、`custom` 或 `package`。
- `module: str | None = None`
- `class_name: str | None = None`
- `prompt: str = "> "`
- `options: dict[str, Any]`

**`TriggerConfig`**

- `type: str`
- `module, class_name: str | None`
- `prompt: str | None = None`
- `options: dict[str, Any]`

**`ToolConfigItem`**

- `name: str`
- `type: str = "builtin"`
- `module, class_name: str | None`
- `doc: str | None = None` — 覆盖 skill 文档路径。
- `options: dict[str, Any]`

**`OutputConfigItem`**

- `type: str = "stdout"`
- `module, class_name: str | None`
- `options: dict[str, Any]`

**`OutputConfig`**

继承 `OutputConfigItem`，并增加：

- `controller_direct: bool = True`
- `named_outputs: dict[str, OutputConfigItem]`

**`SubAgentConfigItem`**

- `name: str`
- `type: str = "builtin"`
- `module, class_name, config_name, description: str | None`
- `tools: list[str]`
- `can_modify: bool = False`
- `interactive: bool = False`
- `options: dict[str, Any]`

### `load_agent_config`

模块：`kohakuterrarium.core.config`。

```python
load_agent_config(config_path: str) -> AgentConfig
```

解析 YAML/JSON/TOML（`config.yaml` → `.yml` → `.json` → `.toml`），并处理 `base_config` 继承、环境变量插值和路径解析。

### `Conversation`, `ConversationConfig`, `ConversationMetadata`

模块：`kohakuterrarium.core.conversation`。

`Conversation` 负责管理消息历史，以及 OpenAI 格式的序列化。

方法：

- `append(role, content, **kwargs) -> Message`
- `append_message(message: Message) -> None`
- `to_messages() -> list[dict]`
- `get_messages() -> MessageList`
- `get_context_length() -> int`
- `get_image_count() -> int`
- `get_system_message() -> Message | None`
- `get_last_message() -> Message | None`
- `get_last_assistant_message() -> Message | None`
- `truncate_from(index: int) -> list[Message]`
- `find_last_user_index() -> int`
- `clear(keep_system: bool = True) -> None`
- `to_json() -> str`
- `from_json(json_str: str) -> Conversation`

`ConversationConfig`：

- `max_messages: int = 0`
- `keep_system: bool = True`

`ConversationMetadata`：

- `created_at, updated_at: datetime`
- `message_count: int = 0`
- `total_chars: int = 0`

### `TriggerEvent`, `EventType`

模块：`kohakuterrarium.core.events`。

在输入、trigger、tool 和 sub-agent 之间传递的通用事件。

字段：

- `type: str`
- `content: EventContent = ""`（`str` 或 `list[ContentPart]`）
- `context: dict[str, Any]`
- `timestamp: datetime`
- `job_id: str | None = None`
- `prompt_override: str | None = None`
- `stackable: bool = True`

方法：

- `get_text_content() -> str`
- `is_multimodal() -> bool`
- `with_context(**kwargs) -> TriggerEvent` — 不会修改原对象。

`EventType` 常量：`USER_INPUT`、`IDLE`、`TIMER`、`CONTEXT_UPDATE`、`TOOL_COMPLETE`、`SUBAGENT_OUTPUT`、`CHANNEL_MESSAGE`、`MONITOR`、`ERROR`、`STARTUP`、`SHUTDOWN`。

工厂函数：

- `create_user_input_event(content, source="cli", **extra_context) -> TriggerEvent`
- `create_tool_complete_event(job_id, content, exit_code=None, error=None, **extra_context) -> TriggerEvent`
- `create_error_event(error_type, message, job_id=None, **extra_context) -> TriggerEvent`
  （`stackable=False`）。

### Channels

模块：`kohakuterrarium.core.channel`。

**`ChannelMessage`**

- `sender: str`
- `content: str | dict | list[dict]`
- `metadata: dict[str, Any]`
- `timestamp: datetime`
- `message_id: str`
- `reply_to: str | None = None`
- `channel: str | None = None`

**`BaseChannel`**（抽象类）

- `async send(message: ChannelMessage) -> None`
- `on_send(callback) -> None`
- `remove_on_send(callback) -> None`
- `channel_type: str` — `"queue"` 或 `"broadcast"`。
- `empty: bool`
- `qsize: int`

**`SubAgentChannel`**（点对点队列）

- `async receive(timeout: float | None = None) -> ChannelMessage`
- `try_receive() -> ChannelMessage | None`

**`AgentChannel`**（广播）

- `subscribe(subscriber_id: str) -> ChannelSubscription`
- `unsubscribe(subscriber_id: str) -> None`
- `subscriber_count: int`

**`ChannelSubscription`**

- `async receive(timeout=None) -> ChannelMessage`
- `try_receive() -> ChannelMessage | None`
- `unsubscribe() -> None`
- `empty, qsize`

**`ChannelRegistry`**

- `get_or_create(name, channel_type="queue", maxsize=0, description="") -> BaseChannel`
- `get(name) -> BaseChannel | None`
- `list_channels() -> list[str]`
- `remove(name) -> bool`
- `get_channel_info() -> list[dict]` — 用于注入到 prompt。

### `Session`, `Scratchpad`, `Environment`

模块：`kohakuterrarium.core.session`、`core.scratchpad`、`core.environment`。

**`Session`**

每个 creature 的共享状态数据类。

- `key: str`
- `channels: ChannelRegistry`
- `scratchpad: Scratchpad`
- `tui: Any | None = None`
- `extra: dict[str, Any]`

模块级函数：

- `get_session(key=None) -> Session`
- `set_session(session, key=None) -> None`
- `remove_session(key=None) -> None`
- `list_sessions() -> list[str]`
- `get_scratchpad() -> Scratchpad`
- `get_channel_registry() -> ChannelRegistry`

**`Scratchpad`**

字符串键值存储。

- `set(key, value) -> None`
- `get(key) -> str | None`
- `delete(key) -> bool`
- `list_keys() -> list[str]`
- `clear() -> None`
- `to_dict() -> dict[str, str]`
- `to_prompt_section() -> str`
- `__len__`, `__contains__`

**`Environment`**

terrarium 的共享执行上下文。

- `env_id: str`
- `shared_channels: ChannelRegistry`
- `get_session(key) -> Session` — creature 私有。
- `list_sessions() -> list[str]`
- `register(key, value) -> None`
- `get(key, default=None) -> Any`

### Jobs

模块：`kohakuterrarium.core.job`。

**`JobType`** 枚举：`TOOL`、`SUBAGENT`、`COMMAND`。

**`JobState`** 枚举：`PENDING`、`RUNNING`、`DONE`、`ERROR`、`CANCELLED`。

**`JobStatus`**

- `job_id: str`
- `job_type: JobType`
- `type_name: str`
- `state: JobState = PENDING`
- `start_time: datetime`
- `end_time: datetime | None = None`
- `output_lines: int = 0`
- `output_bytes: int = 0`
- `preview: str = ""`
- `error: str | None = None`
- `context: dict[str, Any]`

属性：`duration`、`is_complete`、`is_running`。

方法：`to_context_string() -> str`。

**`JobResult`**

- `job_id: str`
- `output: str = ""`
- `exit_code: int | None = None`
- `error: str | None = None`
- `metadata: dict[str, Any]`
- `success: bool` 属性。
- `get_lines(start=0, count=None) -> list[str]`
- `truncated(max_chars=1000) -> str`

**`JobStore`**

- `register(status) -> None`
- `get_status(job_id) -> JobStatus | None`
- `update_status(job_id, state=None, output_lines=None, ...) -> JobStatus | None`
- `store_result(result) -> None`
- `get_result(job_id) -> JobResult | None`
- `get_running_jobs() -> list[JobStatus]`
- `get_pending_jobs() -> list[JobStatus]`
- `get_completed_jobs() -> list[JobStatus]`
- `get_all_statuses() -> list[JobStatus]`
- `format_context(include_completed=False) -> str`

工具函数：

- `generate_job_id(prefix="job") -> str`

### Termination

模块：`kohakuterrarium.core.termination`。

**`TerminationConfig`**

- `max_turns: int = 0`
- `max_tokens: int = 0`（预留）
- `max_duration: float = 0`
- `idle_timeout: float = 0`
- `keywords: list[str]`

**`TerminationChecker`**

- `start() -> None`
- `record_turn() -> None`
- `record_activity() -> None`
- `should_terminate(last_output: str = "") -> bool`
- `reason`、`turn_count`、`elapsed`、`is_active` 属性。

---

## `kohakuterrarium.llm`

### `LLMProvider`（protocol）, `BaseLLMProvider`

模块：`kohakuterrarium.llm.base`。

异步协议：

- `async chat(messages, *, stream=True, tools=None, **kwargs) -> AsyncIterator[str]`
- `async chat_complete(messages, **kwargs) -> ChatResponse`
- 属性 `last_tool_calls: list[NativeToolCall]`

继承 `BaseLLMProvider` 时需要实现：

- `async _stream_chat(messages, *, tools=None, **kwargs)`
- `async _complete_chat(messages, **kwargs) -> ChatResponse`

基类字段：`config: LLMConfig`、`last_usage: dict[str, int]`。

### 消息类型

模块：`kohakuterrarium.llm.base` / `kohakuterrarium.llm.message`。

**`LLMConfig`**

- `model: str`
- `temperature: float = 0.7`
- `max_tokens: int | None = None`
- `top_p: float = 1.0`
- `stop: list[str] | None = None`
- `extra: dict[str, Any] | None = None`

**`ChatChunk`**

- `content: str = ""`
- `finish_reason: str | None = None`
- `usage: dict[str, int] | None = None`

**`ChatResponse`**

- `content, finish_reason, model: str`
- `usage: dict[str, int]`

**`ToolSchema`**

- `name, description: str`
- `parameters: dict[str, Any]`
- `to_api_format() -> dict`

**`NativeToolCall`**

- `id, name, arguments: str`
- `parsed_arguments() -> dict`

**`Message`**

- `role: Role`（`"system"`、`"user"`、`"assistant"`、`"tool"`）
- `content: str | list[ContentPart]`
- `name, tool_call_id: str | None`
- `tool_calls: list[dict] | None`
- `metadata: dict`
- `to_dict() / from_dict(data)`
- `get_text_content() -> str`
- `has_images() -> bool`
- `get_images() -> list[ImagePart]`
- `is_multimodal() -> bool`

子类 `SystemMessage`、`UserMessage`、`AssistantMessage`、`ToolMessage` 会强制固定 role。

**`TextPart`** — `text: str`, `type: "text"`。

**`ImagePart`** — `url, detail ("auto"|"low"|"high"), source_type, source_name`；
`get_description() -> str`。

**`FilePart`** — 文件引用对应类型。

工厂函数：

- `create_message(role, content, **kwargs) -> Message`
- `make_multimodal_content(text, images=None, prepend_images=False) -> str | list[ContentPart]`
- `normalize_content_parts(content) -> str | list[ContentPart] | None`

别名：`Role`、`MessageContent`、`ContentPart`、`MessageList`。

### Profiles

模块：`kohakuterrarium.llm.profiles`、`kohakuterrarium.llm.profile_types`。

**`LLMBackend`** — `name, backend_type, base_url, api_key_env`。

**`LLMPreset`** — `name, model, provider, max_context, max_output, temperature, reasoning_effort, service_tier, extra_body`。

**`LLMProfile`** — preset 和 backend 在运行时合并后的结果：
`name, model, provider, backend_type, max_context, max_output, base_url, api_key_env, temperature, reasoning_effort, service_tier, extra_body`。

模块级函数：

- `load_backends() -> dict[str, LLMBackend]`
- `load_presets() -> dict[str, LLMPreset]`
- `load_profiles() -> dict[str, LLMProfile]`
- `save_backend(backend) -> None`
- `delete_backend(name) -> bool`
- `save_profile(profile) -> None`
- `delete_profile(name) -> bool`
- `get_profile(name) -> LLMProfile | None`
- `get_preset(name) -> LLMProfile | None`
- `get_default_model() -> str`
- `set_default_model(model_name) -> None`
- `resolve_controller_llm(controller_config, llm_override=None) -> LLMProfile | None`
- `list_all() -> list[dict]`

内建 provider 名称：`codex`、`openai`、`openrouter`、`anthropic`、`gemini`、`mimo`。

### API keys

模块：`kohakuterrarium.llm.api_keys`。

- `save_api_key(provider, key) -> None`
- `get_api_key(provider_or_env) -> str`
- `list_api_keys() -> dict[str, str]`（已脱敏）。
- `KT_DIR: Path`
- `KEYS_PATH: Path`
- `PROVIDER_KEY_MAP: dict[str, str]`

---

## `kohakuterrarium.session`

### `SessionStore`

模块：`kohakuterrarium.session.store`。基于 SQLite（KohakuVault）。

表：`meta`、`state`、`events`、`channels`、`subagents`、`jobs`、`conversation`、`fts`。

事件：

- `append_event(agent, event_type, data) -> str`
- `get_events(agent) -> list[dict]`
- `get_resumable_events(agent) -> list[dict]`
- `get_all_events() -> list[tuple[str, dict]]`

对话快照：

- `save_conversation(agent, messages) -> None`
- `load_conversation(agent) -> list[dict] | None`

状态：

- `save_state(agent, *, scratchpad=None, turn_count=None, token_usage=None, triggers=None, compact_count=None) -> None`
- `load_scratchpad(agent) -> dict[str, str]`
- `load_turn_count(agent) -> int`
- `load_token_usage(agent) -> dict[str, int]`
- `load_triggers(agent) -> list[dict]`

Channels：

- `save_channel_message(channel, data) -> str`
- `get_channel_messages(channel) -> list[dict]`

Sub-agents：

- `next_subagent_run(parent, name) -> int`
- `save_subagent(parent, name, run, meta, conv_json=None) -> None`
- `load_subagent_meta(parent, name, run) -> dict | None`
- `load_subagent_conversation(parent, name, run) -> str | None`

Jobs：

- `save_job(job_id, data) -> None`
- `load_job(job_id) -> dict | None`

元数据：

- `init_meta(session_id, config_type, config_path, pwd, agents, config_snapshot=None, terrarium_name=None, terrarium_channels=None, terrarium_creatures=None) -> None`
- `update_status(status) -> None`
- `touch() -> None`
- `load_meta() -> dict[str, Any]`

其他：

- `search(query, k=10) -> list[dict]` — FTS5 BM25。
- `flush() -> None`
- `close(update_status=True) -> None`
- `path: str` 属性。

### `SessionMemory`

模块：`kohakuterrarium.session.memory`。

带索引的搜索（FTS + 向量 + hybrid）。

- `index_events(agent) -> None`
- `async search(query, mode="hybrid", k=5) -> list[SearchResult]`

**`SearchResult`**

- `content: str`
- `round_num, block_num: int`
- `agent: str`
- `block_type: str` — `"text"`、`"tool"`、`"trigger"`、`"user"`。
- `score: float`
- `ts: float`
- `tool_name, channel: str`

### Embedding providers

模块：`kohakuterrarium.session.embedding`。

provider 类型：`model2vec`、`sentence-transformer`、`api`。API
providers 包括 `GeminiEmbedder`。别名：`@tiny`、`@base`、`@retrieval`、`@best`、`@multilingual`、`@multilingual-best`、`@science`、`@nomic`、`@gemma`。

---

## `kohakuterrarium.terrarium`

### `TerrariumRuntime`

模块：`kohakuterrarium.terrarium.runtime`。多 agent 调度器；继承 `HotPlugMixin`。

生命周期：

- `async start() -> None`
- `async stop() -> None`
- `async run() -> None`

热插拔：

- `async add_creature(name, creature: Agent, ...) -> CreatureHandle`
- `async remove_creature(name) -> bool`
- `async add_channel(name, channel_type) -> None`
- `async wire_channel(creature_name, channel_name, direction) -> None`

属性：`api: TerrariumAPI`、`observer: ChannelObserver`。

字段：`config: TerrariumConfig`、`environment: Environment`、`_creatures: dict[str, CreatureHandle]`。

### `TerrariumConfig`, `CreatureConfig`, `ChannelConfig`, `RootConfig`

模块：`kohakuterrarium.terrarium.config`。数据类。

**`TerrariumConfig`**

- `name: str`
- `creatures: list[CreatureConfig]`
- `channels: list[ChannelConfig]`
- `root: RootConfig | None = None`

**`CreatureConfig`**

- `name: str`
- `config_data: dict`
- `base_dir: Path`
- `listen_channels: list[str]`
- `send_channels: list[str]`
- `output_log: bool = False`
- `output_log_size: int = 100`

**`ChannelConfig`**

- `name: str`
- `channel_type: str = "queue"`
- `description: str = ""`

**`RootConfig`**

- `config_data: dict`
- `base_dir: Path`

函数：

- `load_terrarium_config(config_path: str) -> TerrariumConfig`
- `build_channel_topology_prompt(config, creature) -> str`

### `TerrariumAPI`, `ChannelObserver`, `CreatureHandle`

用于编程控制的接口。`TerrariumAPI` 对应 root agent 可用的 terrarium tools。`ChannelObserver` 提供非破坏式观察。`CreatureHandle` 封装了 `Agent` 及其在 terrarium 里的连线信息。

---

## `kohakuterrarium.serving`

### `KohakuManager`

模块：`kohakuterrarium.serving.manager`。与传输层无关的管理器；HTTP API 和任何自定义传输都用它。

Agent 方法：

- `async agent_create(config_path=None, config=None, llm_override=None, pwd=None) -> str`
- `async agent_stop(agent_id) -> None`
- `async agent_chat(agent_id, message) -> AsyncIterator[str]`
- `agent_status(agent_id) -> dict`
- `agent_list() -> list[dict]`
- `agent_interrupt(agent_id) -> None`
- `agent_get_jobs(agent_id) -> list[dict]`
- `async agent_cancel_job(agent_id, job_id) -> bool`
- `agent_switch_model(agent_id, profile_name) -> str`
- `async agent_execute_command(agent_id, command, args="") -> dict`

Terrarium 方法：

- `async terrarium_create(config_path, ...) -> str`
- `async terrarium_stop(terrarium_id) -> None`
- `async terrarium_run(terrarium_id) -> AsyncIterator[str]`
- creature / channel / observer 操作与 HTTP 接口一致。

### `AgentSession`

模块：`kohakuterrarium.serving.agent_session`。对 `Agent` 的轻量封装，支持并发注入输入和流式输出。

工厂方法：

- `async from_path(config_path, llm_override=None, pwd=None) -> AgentSession`
- `async from_config(config: AgentConfig) -> AgentSession`
- `async from_agent(agent: Agent) -> AgentSession`

方法：

- `async start() / async stop()`
- `async chat(message: str | list[dict]) -> AsyncIterator[str]`
- `get_status() -> dict`

字段：`agent_id: str`、`agent: Agent`。

---

## Module protocols（扩展 API）

### `Tool`

模块：`kohakuterrarium.modules.tool.base`。

协议 / `BaseTool` 基类。

- `async execute(args: dict, context: ToolContext | None = None) -> ToolResult` — 必需。
- `needs_context: bool = False`
- `parallel_allowed: bool = True`
- `timeout: float = 60.0`
- `max_output: int = 0`

### `InputModule`

模块：`kohakuterrarium.modules.input.base`。`BaseInputModule` 提供用户命令分发。

- `async start() / async stop()`
- `async get_input() -> TriggerEvent | None`

### `OutputModule`

模块：`kohakuterrarium.modules.output.base`。`BaseOutputModule` 基类。

- `async start() / async stop()`
- `async write(content: str) -> None`
- `async write_stream(chunk: str) -> None`
- `async flush() -> None`
- `async on_processing_start() / async on_processing_end()`
- `on_activity(activity_type: str, detail: str) -> None`
- `async on_user_input(text: str) -> None`（可选）
- `async on_resume(events: list[dict]) -> None`（可选）

活动类型：`tool_start`、`tool_done`、`tool_error`、`subagent_start`、`subagent_done`、`subagent_error`。

### `BaseTrigger`

模块：`kohakuterrarium.modules.trigger.base`。

- `async wait_for_trigger() -> TriggerEvent | None` — 必需。
- `async _on_start() / async _on_stop()` — 可选。
- `_on_context_update(context: dict) -> None` — 可选。
- `resumable: bool = False`
- `universal: bool = False`
- `to_resume_dict() -> dict` / `from_resume_dict(data) -> BaseTrigger`
- `__init__(prompt: str | None = None, **options)`

### `SubAgent`

模块：`kohakuterrarium.modules.subagent.base`。

- `async run(input_text: str) -> SubAgentResult`
- `async cancel() -> None`
- `get_status() -> SubAgentJob`
- `get_pending_count() -> int`

字段：`config: SubAgentConfig`、`llm`、`registry`、`executor`、`conversation`。

`kohakuterrarium.modules.subagent` 中的辅助类：
`SubAgentResult`、`SubAgentJob`、`SubAgentManager`、`InteractiveSubAgent`、`InteractiveManagerMixin`、`SubAgentConfig`。

### Plugin hooks

模块：`kohakuterrarium.modules.plugin`。每个 hook、签名和触发时机见[plugin-hooks.md](/reference/plugin-hooks.md)（英文）。

---

## `kohakuterrarium.compose`

用于组合 agents 和纯函数的 pipeline 代数。

### `BaseRunnable`

- `async run(input) -> Any`
- `async __call__(input) -> Any`
- `__rshift__(other)` — `>>` 顺序执行。
- `__and__(other)` — `&` 并行。
- `__or__(other)` — `|` 兜底。
- `__mul__(n)` — `*` 重试。
- `iterate(initial_input) -> PipelineIterator`
- `map(fn) -> BaseRunnable` — 对输出做后置转换。
- `contramap(fn) -> BaseRunnable` — 对输入做前置转换。
- `fails_when(predicate) -> BaseRunnable`

### 工厂函数

模块：`kohakuterrarium.compose.core`。

- `Pure(fn)` / `pure(fn)` — 包装同步或异步可调用对象。
- `Sequence(*stages)` — 串联。
- `Product(*stages)` — 并行（`asyncio.gather`）。
- `Fallback(*stages)`
- `Retry(stage, attempts)`
- `Router(mapping)` — 基于 dict 的分发。
- `Iterator(...)` — 遍历异步数据源。
- `effects.Effects()` — 记录副作用的句柄。

### Agent 组合

模块：`kohakuterrarium.compose.agent`。

- `async agent(config_path: str) -> AgentRunnable` — 持久 agent，可跨多次调用复用（异步上下文管理器）。
- `factory(config: AgentConfig) -> AgentRunnable` — 临时工厂；每次调用都会新建一个 agent。

运算符优先级：`* > | > & > >>`。

```python
from kohakuterrarium.compose import agent, pure

async with await agent("@kt-defaults/creatures/swe") as swe:
    async with await agent("@kt-defaults/creatures/reviewer") as reviewer:
        pipeline = swe >> pure(extract_code) >> reviewer
        result = await pipeline("Implement feature")
```

---

## `kohakuterrarium.testing`

### `TestAgentBuilder`

模块：`kohakuterrarium.testing.agent`。用于确定性 agent 测试的链式 builder。

builder 方法（返回 `self`）：

- `with_llm_script(script)`
- `with_llm(llm: ScriptedLLM)`
- `with_output(output: OutputRecorder)`
- `with_system_prompt(prompt)`
- `with_session(key)`
- `with_builtin_tools(tool_names)`
- `with_tool(tool)`
- `with_named_output(name, output)`
- `with_ephemeral(ephemeral=True)`
- `build() -> TestAgentEnv`

`TestAgentEnv`：

- 属性：`llm: ScriptedLLM`、`output: OutputRecorder`、`session: Session`。
- 方法：`async inject(content)`、`async chat(content) -> str`。

### `ScriptedLLM`

模块：`kohakuterrarium.testing.llm`。

构造函数：`ScriptedLLM(script: list[ScriptEntry] | list[str] | None = None)`。

**`ScriptEntry`**：`response: str`、`match: str | None = None`、`delay_per_chunk: float = 0`、`chunk_size: int = 10`。

方法：`async chat`、`async chat_complete`。

断言接口：`call_count: int`、`call_log: list[list[dict]]`。

### `OutputRecorder`

模块：`kohakuterrarium.testing.output`。

- `all_text: str`
- `chunks: list[str]`
- `writes: list[str]`
- `activities: list[tuple[str, str]]`

### `EventRecorder`

模块：`kohakuterrarium.testing.events`。

- `record(event) -> None`
- `get_all() -> list[TriggerEvent]`
- `get_by_type(event_type) -> list[TriggerEvent]`
- `clear() -> None`

---

## Packages

模块：`kohakuterrarium.packages`。

- `is_package_ref(path: str) -> bool`
- `resolve_package_path(ref: str) -> Path`
- `list_packages() -> list[str]`
- `install_package(source, name=None, editable=False) -> None`
- `uninstall_package(name) -> bool`

包根目录：`~/.kohakuterrarium/packages/`。可编辑安装不会复制文件，而是使用 `<name>.link` 指针。

---

## 另见

- 概念：
  [composing an agent](/concepts/foundations/composing-an-agent.md)（英文）、
  [modules/tool](/concepts/modules/tool.md)（英文）、
  [modules/sub-agent](/concepts/modules/sub-agent.md)（英文）、
  [impl-notes/session-persistence](/concepts/impl-notes/session-persistence.md)（英文）。
- 指南：
  [programmatic usage](/guides/programmatic-usage.md)（英文）、
  [custom modules](/guides/custom-modules.md)（英文）、
  [plugins](/guides/plugins.md)（英文）。
- 参考：
  [cli](/reference/cli.md)（英文）、
  [http](/reference/http.md)（英文）、
  [configuration](/reference/configuration.md)（英文）、
  [builtins](/reference/builtins.md)（英文）、
  [plugin-hooks](/reference/plugin-hooks.md)（英文）。
