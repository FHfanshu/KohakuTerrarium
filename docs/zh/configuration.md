# Configuration

给已经有 creature，想改一改；或者准备接一个新的，但又不想去啃完整 reference 的人看。

Creature 配置用 YAML 写，也支持 JSON/TOML。每个顶层 key 都对应 `AgentConfig` 的一个字段；`controller`、`input`、`output` 这类子块各自也是 dataclass，有自己的字段。这篇按事情来讲。要看完整字段列表，去 [reference/configuration](../reference/configuration.md)。

先补一下概念： [creatures](creatures.md)、[composing an agent](../concepts/foundations/composing-an-agent.md)。

环境变量插值哪里都能用：`${VAR}` 或 `${VAR:default}`。

## 怎么切换模型？

先从 `~/.kohakuterrarium/llm_profiles.yaml` 里挑一个预设；没有就用 `kt config llm add` 加：

```yaml
controller:
  llm: claude-opus-4.6
  reasoning_effort: high
```

也可以只在这次运行里临时覆盖：

```bash
kt run path/to/creature --llm gpt-5.4
```

如果你想把设置全写在配置里，不走 profile 文件，那就用 `model` + `api_key_env` + `base_url`：

```yaml
controller:
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
  base_url: https://api.openai.com/v1
  temperature: 0.3
```

## 怎么继承一个开箱即用的 creature？

```yaml
name: my-swe
base_config: "@kt-defaults/creatures/swe"
controller:
  reasoning_effort: xhigh
tools:
  - name: my_tool
    type: custom
    module: ./tools/my_tool.py
```

标量字段直接覆盖；`controller`、`input`、`output` 会合并；列表会按 `name` 扩展并去重。如果你不想扩展，而是整列替换：

```yaml
no_inherit: [tools, subagents]
```

## 怎么加一个 tool？

内置工具可以直接写短名字：

```yaml
tools:
  - bash
  - read
  - web_search
```

要带参数就这样写：

```yaml
tools:
  - name: web_search
    options:
      max_results: 10
      region: us-en
```

自定义 tool（本地模块）：

```yaml
tools:
  - name: my_tool
    type: custom
    module: ./tools/my_tool.py
    class_name: MyTool
```

包里的 tool（来自已安装包的 `kohaku.yaml`）：

```yaml
tools:
  - name: kql
    type: package
```

协议怎么写，看 [Custom Modules](custom-modules.md)。

## 怎么加一个子 agent？

```yaml
subagents:
  - plan
  - worker
  - name: my_critic
    type: custom
    module: ./subagents/critic.py
    config_name: CRITIC_CONFIG
    interactive: true       # 父 agent 换轮次后它也会继续活着
    can_modify: true
```

内置的有：`worker`、`coordinator`、`explore`、`plan`、`research`、`critic`、`response`、`memory_read`、`memory_write`、`summarize`。

## 怎么加 trigger？

```yaml
triggers:
  - type: timer
    options: { interval: 300 }
    prompt: "Check for pending tasks."
  - type: channel
    options: { channel: alerts }
  - type: idle
    options: { timeout: 120 }
    prompt: "If the user seems stuck, ask."
```

内置类型有：`timer`、`idle`、`webhook`、`channel`、`custom`、`package`。trigger 触发时，`prompt` 会注入到 `TriggerEvent.prompt_override`。

## 怎么设置 compaction？

```yaml
compact:
  enabled: true
  threshold: 0.8
  target: 0.5
  keep_recent_turns: 5
  compact_model: gpt-4o-mini
```

它具体做什么，看 [Sessions](sessions.md)。

## 怎么加自定义 input？

```yaml
input:
  type: custom
  module: ./inputs/discord.py
  class_name: DiscordInput
  options:
    token: "${DISCORD_TOKEN}"
    channel_id: 123456
```

内置类型有：`cli`、`tui`、`asr`、`whisper`、`none`。协议见 [Custom Modules](custom-modules.md)。

## 怎么加一个带名字的输出通道？

当 tool 或子 agent 想把内容发到某个指定通道时，这个很有用，比如 TTS、Discord、文件：

```yaml
output:
  type: stdout
  named_outputs:
    tts:
      type: tts
      options: { provider: edge, voice: en-US-AriaNeural }
    discord:
      type: custom
      module: ./outputs/discord.py
      class_name: DiscordOutput
      options: { webhook_url: "${DISCORD_WEBHOOK}" }
```

## 怎么用 plugin 给 tool 加一道限制？

下面这个生命周期插件会拦危险命令：

```yaml
plugins:
  - name: tool_guard
    type: custom
    module: ./plugins/tool_guard.py
    class: ToolGuard
    options:
      deny_patterns: ["rm -rf", "dd if="]
```

插件类怎么写，看 [Plugins](plugins.md)。参考实现看 [examples/plugins/tool_guard.py](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/examples/plugins/tool_guard.py)。

## 怎么注册 MCP 服务器？

按 creature 配：

```yaml
mcp_servers:
  - name: sqlite
    transport: stdio
    command: mcp-server-sqlite
    args: ["/var/db/my.db"]
  - name: docs_api
    transport: http
    url: https://mcp.example.com/sse
    env: { API_KEY: "${DOCS_API_KEY}" }
```

全局配置 `~/.kohakuterrarium/mcp_servers.yaml` 用的是同一套格式。见 [MCP](mcp.md)。

## 怎么改 tool 调用格式？

```yaml
tool_format: bracket        # default: [/name]@@arg=value\n[name/]
# or
tool_format: xml            # <name arg="value"></name>
# or
tool_format: native         # provider-native function calling
```

每种格式具体长什么样，看 [creatures guide — Tool format](creatures.md)；如果你想自定义分隔符，看 [reference/configuration.md — `tool_format`](../reference/configuration.md)。

## 怎么选 dynamic 还是 static skill mode？

```yaml
skill_mode: dynamic   # 默认，`info` 框架命令按需加载完整文档
# or
skill_mode: static    # 完整 tool 文档直接塞进 system prompt
```

## 怎么让 creature 在没有用户输入时也一直活着？

```yaml
input:
  type: none
triggers:
  - type: timer
    options: { interval: 60 }
    prompt: "Check for anomalies."
```

`none` input 加任意 trigger，就是标准的监控 agent 写法。

## 怎么给一次运行加边界？

```yaml
termination:
  max_turns: 15
  max_duration: 600
  idle_timeout: 120
  keywords: ["DONE", "ABORT"]
```

其中任意一个条件满足，agent 就会停。

## 怎么让多个 creature 共享状态（不通过 terrarium）？

给它们同一个 `session_key`：

```yaml
name: writer
session_key: shared-workspace
---
name: reviewer
session_key: shared-workspace
```

这样两个 creature 会共享 `Scratchpad` 和 `ChannelRegistry`。适合同一个进程里跑多个 creature，但又没用 terrarium 的情况。

## 怎么配 memory / embedding？

```yaml
memory:
  embedding:
    provider: model2vec
    model: "@retrieval"
```

见 [Memory](memory.md)。

## 怎么把 creature 固定到某个工作目录？

```bash
kt run path/to/creature --pwd /path/to/project
```

`pwd` 会传给每个 tool 的 `ToolContext`。

## 排错

- **环境变量没展开。** 要写 `${VAR}`，花括号不能省。`$VAR` 会被当普通字符串。
- **子配置里像是“丢了”父配置的 tool。** 你写了 `no_inherit: [tools]`。删掉它，列表就会改成扩展。
- **配置能加载，但 tool 没出现。** 短名字会去内置工具目录里找，拼错了通常不会报得很明显。用 `kt info path/to/creature` 看看。
- **两个设置打架。** CLI 覆盖项（比如 `--llm`）优先于配置；配置又优先于 `llm_profiles.yaml` 里的 `default_model`。

## 另见

- [Reference / configuration](../reference/configuration.md) —— 所有字段、类型和默认值。
- [Creatures](creatures.md) —— 目录结构和组成。
- [Plugins](plugins.md)、[Custom Modules](custom-modules.md)、[MCP](mcp.md)、[Memory](memory.md) —— 各块怎么接。