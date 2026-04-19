# 配置

这里汇总了 creature、terrarium、LLM profile、MCP server 和 package manifest 的全部配置字段。文件格式支持 YAML（推荐）、JSON、TOML。所有文件都支持 `${VAR}` / `${VAR:default}` 环境变量插值，加载时生效。

想看 creature 和 terrarium 的关系模型，见 [concepts/boundaries](/concepts/boundaries.md)。想看实际示例，见 [guides/configuration](//zh/guides/configuration.md)和 [guides/creatures](//zh/guides/creatures.md)。

## 路径解析

配置字段如果引用了其他文件或 package，按下面的顺序解析：

1. `@<pkg>/<path-inside-pkg>` → `~/.kohakuterrarium/packages/<pkg>/<path-inside-pkg>`
   （可编辑安装时会跟随 `<pkg>.link`）。
2. `creatures/<name>` 这类相对项目的写法 → 从当前 agent 文件夹向上查找项目根目录。
3. 其他情况 → 相对当前 agent 文件夹解析；如果是继承来的配置，则回退到 base-config 所在文件夹。

---

## Creature 配置（`config.yaml`）

由 `kohakuterrarium.core.config.load_agent_config` 加载。文件查找顺序：`config.yaml` → `config.yml` → `config.json` → `config.toml`。

### 顶层字段

| 字段 | 类型 | 默认值 | 必填 | 说明 |
|---|---|---|---|---|
| `name` | str | — | 是 | Creature 名称。如果没有设置 `session_key`，它也会作为默认 session key。 |
| `version` | str | `"1.0"` | 否 | 说明性字段。 |
| `base_config` | str | `null` | 否 | 要继承的父配置（`@package/path`、`creatures/<name>` 或相对路径）。 |
| `controller` | dict | `{}` | 否 | LLM/controller 配置块。见 [Controller](#controller-块)。 |
| `system_prompt` | str | `"You are a helpful assistant."` | 否 | 内联 system prompt。 |
| `system_prompt_file` | str | `null` | 否 | Markdown prompt 文件路径；相对 agent 文件夹。继承链上会按顺序拼接。 |
| `prompt_context_files` | dict[str,str] | `{}` | 否 | Jinja 变量 → 文件路径；渲染 prompt 时会读取这些文件并注入。 |
| `skill_mode` | str | `"dynamic"` | 否 | `dynamic`（按需，通过 `info` 框架命令）或 `static`（一开始提供完整文档）。 |
| `include_tools_in_prompt` | bool | `true` | 否 | 是否包含自动生成的工具列表。 |
| `include_hints_in_prompt` | bool | `true` | 否 | 是否包含框架提示（tool-call 语法，以及 `info` / `read_job` / `jobs` / `wait` 命令示例）。 |
| `max_messages` | int | `0` | 否 | 对话上限。`0` 表示不限。 |
| `ephemeral` | bool | `false` | 否 | 每轮后清空对话（群聊模式）。 |
| `session_key` | str | `null` | 否 | 覆盖默认 session key（默认值是 `name`）。 |
| `input` | dict | `{}` | 否 | 输入模块配置。见 [Input](#input)。 |
| `output` | dict | `{}` | 否 | 输出模块配置。见 [Output](#output)。 |
| `tools` | list | `[]` | 否 | 工具条目。见 [Tools](#tools)。 |
| `subagents` | list | `[]` | 否 | 子 agent 条目。见 [Sub-agents](#sub-agents)。 |
| `triggers` | list | `[]` | 否 | 触发器条目。见 [Triggers](#triggers)。 |
| `compact` | dict | `null` | 否 | 压缩配置。见 [Compact](#compact)。 |
| `startup_trigger` | dict | `null` | 否 | 启动时触发一次的触发器。格式：`{prompt: "..."}`。 |
| `termination` | dict | `null` | 否 | 终止条件。见 [Termination](#termination)。 |
| `max_subagent_depth` | int | `3` | 否 | 子 agent 最大嵌套深度。`0` 表示不限。 |
| `tool_format` | str \| dict | `"bracket"` | 否 | `bracket`、`xml`、`native`，或自定义 dict 格式。 |
| `mcp_servers` | list | `[]` | 否 | 每个 agent 自己的 MCP server。见 [MCP servers](#agent-配置中的-mcp-servers)。 |
| `plugins` | list | `[]` | 否 | 生命周期插件。见 [Plugins](#plugins)。 |
| `no_inherit` | list[str] | `[]` | 否 | 这些键会直接替换 base 值，而不是合并。例如 `[tools, subagents]`。 |
| `memory` | dict | `{}` | 否 | `memory.embedding.{provider,model}`。见 [Memory](#memory)。 |
| `output_wiring` | list | `[]` | 否 | 每个 creature 的自动回合输出路由。见 [输出路由](#输出路由)。 |

### Controller 块

为了兼容旧配置，这些字段也可以直接写在顶层。

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `llm` | str | `""` | `~/.kohakuterrarium/llm_profiles.yaml` 中的 profile 引用（例如 `gpt-5.4`、`claude-opus-4.6`）。 |
| `model` | str | `""` | 如果没有设置 `llm`，可直接写模型 id。 |
| `auth_mode` | str | `""` | 留空（自动）、`codex-oauth` 等。 |
| `api_key_env` | str | `""` | 保存 key 的环境变量名。 |
| `base_url` | str | `""` | 覆盖 endpoint URL。 |
| `temperature` | float | `0.7` | 采样温度。 |
| `max_tokens` | int \| null | `null` | 输出上限。 |
| `reasoning_effort` | str | `"medium"` | `none`、`minimal`、`low`、`medium`、`high`、`xhigh`。 |
| `service_tier` | str | `null` | `priority`、`flex`。 |
| `extra_body` | dict | `{}` | 原样合并进请求 JSON。 |
| `skill_mode`, `include_tools_in_prompt`, `include_hints_in_prompt`, `max_messages`, `ephemeral`, `tool_format` | | | 与顶层同名字段含义一致。 |

每轮请求的解析顺序：

1. `--llm` CLI 参数。
2. `controller.llm`。
3. `controller.model`（外加可选的 `base_url` / `api_key_env`）。
4. `llm_profiles.yaml` 中的 `default_model`。

### Input

字段结构：`{type, module?, class_name?, options?, ...type-specific keys}`。

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `type` | str | `"cli"` | `cli`、`tui`、`asr`、`whisper`、`none`、`custom`、`package`。 |
| `module` | str | — | `custom` 时使用（例如 `./custom/input.py`），或 `package` 时使用（例如 `pkg.mod`）。 |
| `class_name` | str | — | 要实例化的类名。 |
| `options` | dict | `{}` | 模块专用选项。 |
| `prompt` | str | `"> "` | CLI prompt（cli input）。 |
| `exit_commands` | list[str] | `[]` | 触发退出的字符串。 |

### Output

支持一个默认输出，另外还可以通过 `named_outputs` 配置额外的侧路输出（例如 Discord webhook）。

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `type` | str | `"stdout"` | `stdout`、`tts`、`tui`、`custom`、`package`。 |
| `module` | str | — | `custom` / `package` 输出模块使用。 |
| `class_name` | str | — | 要实例化的类名。 |
| `options` | dict | `{}` | 模块专用选项。 |
| `controller_direct` | bool | `true` | 把 controller 文本路由到默认输出。 |
| `named_outputs` | dict[str, OutputConfigItem] | `{}` | 命名侧路输出。每一项的结构都和默认输出一样。 |

### Tools

工具列表。每一项可以写成一个 dict，也可以直接写字符串简写，表示同名 builtin。

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `name` | str | — | 工具名（必填）。 |
| `type` | str | `"builtin"` | `builtin`、`custom`、`package`。 |
| `module` | str | — | `custom` 时使用（例如 `./custom/tools/my_tool.py`），或 `package` 时使用。 |
| `class_name` | str | — | 要实例化的类名。 |
| `doc` | str | — | 覆盖 skill 文档文件。 |
| `options` | dict | `{}` | 工具专用选项。 |

简写：

```yaml
tools:
  - bash
  - read
  - write
```

### Sub-agents

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `name` | str | — | 子 agent 标识符。 |
| `type` | str | `"builtin"` | `builtin`、`custom`、`package`。 |
| `module` | str | — | `custom` / `package` 使用。 |
| `config_name` | str | — | 模块内部的命名配置对象（例如 `MY_AGENT_CONFIG`）。 |
| `description` | str | — | 用在父 agent prompt 里的描述。 |
| `tools` | list[str] | `[]` | 这个子 agent 允许使用的工具。 |
| `can_modify` | bool | `false` | 子 agent 是否可以执行会修改状态的操作。 |
| `interactive` | bool | `false` | 是否跨轮保持存活，并接收上下文更新。 |
| `options` | dict | `{}` | 子 agent 专用选项。 |

### Triggers

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `type` | str | — | `timer`、`idle`、`webhook`、`channel`、`custom`、`package`。 |
| `module` | str | — | `custom` / `package` 使用。 |
| `class_name` | str | — | 要实例化的类名。 |
| `prompt` | str | — | 触发器触发时默认注入的 prompt。 |
| `options` | dict | `{}` | 触发器专用选项。 |

各类型常见选项：

- `timer`：`interval`（秒）。
- `idle`：`timeout`（秒）。
- `channel`：channel 名称和过滤条件。
- `webhook`：endpoint 设置。

### Compact

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `enabled` | bool | `true` | 是否开启压缩。 |
| `max_tokens` | int | profile-default | 目标 token 上限。 |
| `threshold` | float | `0.8` | 达到 `max_tokens` 的这个比例后开始压缩。 |
| `target` | float | `0.5` | 压缩后的目标比例。 |
| `keep_recent_turns` | int | `5` | 原样保留的最近轮数。 |
| `compact_model` | str | controller's model | 用于总结压缩的 LLM；可覆盖默认值。 |

### 输出路由

这是一个框架层的路由列表。每当 creature 一轮结束，框架都会构造一个 `creature_output` `TriggerEvent`，直接推到每个目标 creature 的事件队列里，完全绕过 channel。关于用法上的讨论，见 [Terrariums 指南里的输出路由](//zh/guides/terrariums.md#输出路由) 和 [patterns.md 里的模式 1b](/zh/concepts/patterns.md)；这里主要讲配置本身。

每个条目的字段：

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `to` | str | — | 目标 creature 名，或者特殊字符串 `"root"`。 |
| `with_content` | bool | `true` | 如果是 `false`，事件里的 `content` 会是空字符串，只发元数据 ping。 |
| `prompt` | str \| null | `null` | 接收侧 prompt override 的模板。不填时，会根据 `with_content` 套默认模板。 |
| `prompt_format` | `simple` \| `jinja` | `"simple"` | `simple` 用 `str.format_map`；`jinja` 用 `prompt.template` 的渲染器，适合条件和过滤。 |

两个格式都能用的模板变量有：`source`、`target`、`content`、`turn_index`、`source_event_type`、`with_content`。

简写规则：如果直接写字符串，就等价于 `{to: <str>, with_content: true}`：

```yaml
output_wiring:
  - runner                                   # 简写
  - { to: root, with_content: false }        # 生命周期 ping
  - to: analyzer
    prompt: "[From coder] {content}"         # simple（默认）
  - to: critic
    prompt: "{{ source | upper }}: {{ content }}"
    prompt_format: jinja
```

几点说明：

- 只有 creature 运行在 terrarium 里时，这个配置才真的有意义。单独运行的 creature 就算配了 `output_wiring`，也不会真的发出去（resolver 是 terrarium runtime 挂上的；独立 agent 只会拿到一个 no-op resolver，并记录一次日志）。
- 目标不存在，或者目标已经停了，只会记日志并跳过，不会把异常往源 creature 的回合收尾流程里抛。
- 源 creature 的 `_finalize_processing` 会直接收尾完成；每个目标的 `_process_event` 都在自己的 `asyncio.Task` 里跑，所以接收方慢，不会反过来卡住发送方。

### Termination

只要阈值不是 0，就会生效。关键字匹配会在输出包含该关键字时停止 agent。

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `max_turns` | int | `0` | |
| `max_tokens` | int | `0` | |
| `max_duration` | float | `0` | 秒。 |
| `idle_timeout` | float | `0` | 无事件持续的秒数。 |
| `keywords` | list[str] | `[]` | 区分大小写的子串匹配。 |

### Agent 配置中的 MCP servers

每个 agent 自己配置的 MCP server。agent 启动时连接。

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `name` | str | — | server 标识符。 |
| `transport` | `stdio` \| `http` | — | 传输方式。 |
| `command` | str | — | `stdio` 可执行文件。 |
| `args` | list[str] | `[]` | `stdio` 参数。 |
| `env` | dict[str,str] | `{}` | `stdio` 环境变量。 |
| `url` | str | — | HTTP/SSE endpoint。 |

### Plugins

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `name` | str | — | 插件标识符。 |
| `type` | str | `"builtin"` | `builtin`、`custom`、`package`。 |
| `module` | str | — | `custom` 时使用（例如 `./custom/plugins/my.py`），或 `package` 时使用。 |
| `class` 或 `class_name` | str | — | 要实例化的类名。 |
| `description` | str | — | 自由格式元数据。 |
| `options` | dict | `{}` | 插件专用选项。 |

简写：单独一个字符串会被当作按 package 解析的插件名。

### Memory

```yaml
memory:
  embedding:
    provider: model2vec       # 或 sentence-transformer、api
    model: "@best"            # 预设别名或 HuggingFace 路径
```

Provider 选项：

- `model2vec`（默认，不依赖 torch）。
- `sentence-transformer`（基于 torch，质量更高）。

预设别名：`@tiny`、`@base`、`@retrieval`、`@best`、`@multilingual`、`@multilingual-best`、`@science`、`@nomic`、`@gemma`。

### 继承规则

`base_config` 按前面的路径规则解析。所有字段都使用同一套合并规则：

- **标量** —— 子配置覆盖父配置。
- **Dict**（`controller`、`input`、`output`、`memory`、`compact` 等）—— 浅合并；顶层同名键由子配置覆盖。
- **按标识键合并的列表**（`tools`、`subagents`、`plugins`、`mcp_servers`、`triggers`）—— 按 `name` 做并集。名字冲突时，**子配置优先**，并在原位置替换父项（保留父配置顺序）。没有 `name` 的项直接拼接。
- **其他列表** —— 子配置直接替换父配置。
- **Prompt 文件** —— `system_prompt_file` 会沿继承链拼接；内联 `system_prompt` 最后追加。

下面两个指令可以跳过默认行为：

| 指令 | 作用 |
|-----------|--------|
| `no_inherit: [field, …]` | 丢弃列出的每个字段的继承值。对标量、dict、标识列表和 prompt 链都一样生效。 |
| `prompt_mode: concat \| replace` | `concat`（默认）保留继承来的 prompt 文件链和内联 prompt。`replace` 会清空继承来的 prompt；这是 `no_inherit: [system_prompt, system_prompt_file]` 的简写。 |

**示例。**

覆盖继承来的某个工具，不必替换整个列表：

```yaml
base_config: "@kt-biome/creatures/swe"
tools:
  - { name: bash, type: custom, module: ./tools/safe_bash.py, class: SafeBash }
```

从空开始：完全丢弃继承来的工具。

```yaml
base_config: "@kt-biome/creatures/general"
no_inherit: [tools]
tools:
  - { name: think, type: builtin }
```

为某个特化 persona 完全替换 prompt：

```yaml
base_config: "@kt-biome/creatures/general"
prompt_mode: replace
system_prompt_file: prompts/niche.md
```

### 文件约定

```
creatures/<name>/
  config.yaml           # 必需
  prompts/system.md     # 如果有引用
  tools/                # 自定义工具模块
  memory/               # 上下文文件
  subagents/            # 自定义子 agent 配置
```

---

## Terrarium 配置（`terrarium.yaml`）

由 `kohakuterrarium.terrarium.config.load_terrarium_config` 加载。

```yaml
terrarium:
  name: str
  root:                  # 可选 — terrarium 外部的 root agent
    base_config: str     # 或直接内联任意 AgentConfig 字段
    ...
  creatures:
    - name: str
      base_config: str   # 旧别名：`config:`
      channels:
        listen: [str]
        can_send: [str]
      output_log: bool         # 默认 false
      output_log_size: int     # 默认 100
      ...                      # 任意 AgentConfig 覆盖字段
  channels:
    <name>:
      type: queue | broadcast  # 默认 queue
      description: str
    # 或简写 — 字符串就是 description：
    # <name>: "description"
```

Terrarium 字段汇总：

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `name` | str | — | Terrarium 名称。 |
| `root` | object | `null` | 可选的 root-agent 配置。这个 agent 会被强制加上 terrarium 管理工具。 |
| `creatures` | list | `[]` | 在 terrarium 内运行的 creatures。 |
| `channels` | dict | `{}` | 共享 channel 声明。 |

Creature 条目字段（这里也可以直接内联任何 AgentConfig 字段，比如 `system_prompt_file`、`controller`、`output_wiring` 等）：

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `name` | str | — | Creature 名称。 |
| `base_config`（或 `config`） | str | — | 配置路径（agent config）。 |
| `channels.listen` | list[str] | `[]` | 这个 creature 监听的 channels。 |
| `channels.can_send` | list[str] | `[]` | 这个 creature 可以发布到的 channels。 |
| `output_log` | bool | `false` | 按 creature 捕获 stdout。 |
| `output_log_size` | int | `100` | 每个 creature 日志缓冲区的最大行数。 |
| `output_wiring` | list | `[]` | 框架级自动投递：把这个 creature 的回合结束输出自动送给别的 creatures。条目格式见 [输出路由](#输出路由)。 |

Channel 条目字段：

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `type` | `queue` \| `broadcast` | `queue` | 投递语义。 |
| `description` | str | `""` | 会写进 channel 拓扑 prompt。 |

自动创建的 channels：

- 每个 creature 都有一个同名 `queue`（私信通道）。
- 如果设置了 `root`，还会创建 `report_to_root` queue。

Root agent：

- 会获得带有 `terrarium_*` 和 `creature_*` 工具的 `TerrariumToolManager`。
- 自动监听所有 creature channel，并接收 `report_to_root`。
- 继承和合并规则与 creature 相同。

---

## LLM profiles（`~/.kohakuterrarium/llm_profiles.yaml`）

```yaml
version: 3
default_model: <preset name>

backends:
  <provider-name>:
    backend_type: openai | codex | anthropic
    base_url: str
    api_key_env: str

presets:
  <preset-name>:
    provider: <backend-name>   # 引用 backends 或内建 provider
    model: str                 # model id
    max_context: int           # 默认 256000
    max_output: int            # 默认 65536
    temperature: float         # 可选
    reasoning_effort: str      # none | minimal | low | medium | high | xhigh
    service_tier: str          # priority | flex
    extra_body: dict
```

内建 provider 名称（不可覆盖）：`codex`、`openai`、`openrouter`、`anthropic`、`gemini`、`mimo`。

全部内置 preset 见 [builtins.md — LLM presets](/reference/builtins.md#llm-presets)。

---

## MCP server 目录（`~/.kohakuterrarium/mcp_servers.yaml`）

全局 MCP 注册表，可替代每个 agent 单独配置的 `mcp_servers:`。

```yaml
- name: sqlite
  transport: stdio
  command: mcp-server-sqlite
  args: ["/path/to/db"]
  env: {}
- name: web_api
  transport: http
  url: https://mcp.example.com/sse
  env: { API_KEY: ${MCP_API_KEY} }
```

字段：

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `name` | str | — | 唯一标识符。 |
| `transport` | `stdio` \| `http` | — | 传输方式。 |
| `command` | str | — | `stdio` 可执行文件。 |
| `args` | list[str] | `[]` | `stdio` 参数。 |
| `env` | dict[str,str] | `{}` | `stdio` 环境变量。 |
| `url` | str | — | `http` 传输方式使用的 HTTP endpoint。 |

---

## Package manifest（`kohaku.yaml`）

```yaml
name: my-package
version: "1.0.0"
description: "..."
creatures:
  - name: researcher
terrariums:
  - name: research_team
tools:
  - name: my_tool
    module: my_package.tools
    class: MyTool
plugins:
  - name: my_plugin
    module: my_package.plugins
    class: MyPlugin
llm_presets:
  - name: my_preset
python_dependencies:
  - requests>=2.28.0
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | str | Package 名称；安装路径为 `~/.kohakuterrarium/packages/<name>/`。 |
| `version` | str | Semver。 |
| `description` | str | 自由格式说明。 |
| `creatures` | list | `[{name}]` —— 位于 `creatures/<name>/` 下的 creature 配置。 |
| `terrariums` | list | `[{name}]` —— 位于 `terrariums/<name>/` 下的 terrarium 配置。 |
| `tools` | list | `[{name, module, class}]` —— package 提供的工具类。 |
| `plugins` | list | `[{name, module, class}]` —— package 提供的插件。 |
| `llm_presets` | list | `[{name}]` —— package 提供的 LLM preset（具体值保存在 package 内）。 |
| `python_dependencies` | list[str] | Pip requirement 字符串。 |

安装方式：

- `kt install <git_url>` —— clone。
- `kt install <path>` —— copy。
- `kt install <path> -e` —— 写入指向源码的 `<name>.link` 指针文件。

---

## API key 存储（`~/.kohakuterrarium/api_keys.yaml`）

这部分由 `kt login` 和 `kt config key set` 管。格式如下：

```yaml
openai: sk-...
openrouter: sk-or-...
anthropic: sk-ant-...
```

解析顺序：已存储文件 → 环境变量（`api_key_env`）→ 空值。

---

## 另见

- 概念：[boundaries](/concepts/boundaries.md)、[composing an agent](/concepts/foundations/composing-an-agent.md)、[multi-agent overview](/concepts/multi-agent/README.md)。
- 指南：[configuration](//zh/guides/configuration.md)、[creatures](//zh/guides/creatures.md)、[terrariums](//zh/guides/terrariums.md)。
- 参考：[cli](/reference/cli.md)、[builtins](/reference/builtins.md)、[python](/reference/python.md)。
