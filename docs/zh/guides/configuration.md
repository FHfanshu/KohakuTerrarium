# 配置

这篇给想改现有 creature，或者新接一个 creature、但不想先把配置参考逐字段读完的人看。

Creature 配置用 YAML，也支持 JSON/TOML。每个顶层键都对应 `AgentConfig` 的一个字段；`controller`、`input`、`output` 这类子块各自也有字段。这里按任务讲，完整字段列表见 [configuration](/reference/configuration.md)（英文）。

先看概念： [creatures](/guides/creatures.md)（英文）、[composing an agent](/concepts/foundations/composing-an-agent.md)（英文）。

环境变量插值在任何位置都能用：`${VAR}` 或 `${VAR:default}`。

## 怎么切换模型？

从 `~/.kohakuterrarium/llm_profiles.yaml` 里选一个 preset；没有就用 `kt config llm add` 新增：

```yaml
controller:
  llm: claude-opus-4.6
  reasoning_effort: high
```

也可以只在单次运行时通过命令行覆盖：

```bash
kt run path/to/creature --llm gpt-5.4
```

如果你想把设置全写在配置里，不用 profile 文件，就填 `model`、`api_key_env` 和 `base_url`：

```yaml
controller:
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
  base_url: https://api.openai.com/v1
  temperature: 0.3
```

## 怎么继承 OOTB creature？

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

标量字段直接覆盖；`controller`、`input`、`output` 会合并；列表会扩展，并按 `name` 去重。想替换列表而不是扩展，就写：

```yaml
no_inherit: [tools, subagents]
```

## 怎么加工具？

内置工具可以用简写：

```yaml
tools:
  - bash
  - read
  - web_search
```

带选项时：

```yaml
tools:
  - name: web_search
    options:
      max_results: 10
      region: us-en
```

自定义工具（本地模块）：

```yaml
tools:
  - name: my_tool
    type: custom
    module: ./tools/my_tool.py
    class_name: MyTool
```

包工具（从已安装包的 `kohaku.yaml` 读取）：

```yaml
tools:
  - name: kql
    type: package
```

协议见 [Custom Modules](/guides/custom-modules.md)（英文）。

## 怎么加子 agent？

```yaml
subagents:
  - plan
  - worker
  - name: my_critic
    type: custom
    module: ./subagents/critic.py
    config_name: CRITIC_CONFIG
    interactive: true       # 在父 agent 的多轮之间保持存活
    can_modify: true
```

内置项：`worker`、`coordinator`、`explore`、`plan`、`research`、`critic`、`response`、`memory_read`、`memory_write`、`summarize`。

## 怎么加触发器？

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

内置类型有 `timer`、`idle`、`webhook`、`channel`、`custom`、`package`。触发器触发时，`prompt` 会注入为 `TriggerEvent.prompt_override`。

## 怎么设置 compaction？

```yaml
compact:
  enabled: true
  threshold: 0.8
  target: 0.5
  keep_recent_turns: 5
  compact_model: gpt-4o-mini
```

compaction 的作用见 [Sessions](/guides/sessions.md)（英文）。

## 怎么加自定义输入？

```yaml
input:
  type: custom
  module: ./inputs/discord.py
  class_name: DiscordInput
  options:
    token: "${DISCORD_TOKEN}"
    channel_id: 123456
```

内置类型：`cli`、`tui`、`asr`、`whisper`、`none`。协议见 [Custom Modules](/guides/custom-modules.md)（英文）。

## 怎么加具名输出通道？

当工具或子 agent 需要把输出发到特定通道时，这个配置很有用，比如 TTS、Discord、文件：

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

## 怎么用插件限制工具？

下面这个生命周期插件会拦住危险命令：

```yaml
plugins:
  - name: tool_guard
    type: custom
    module: ./plugins/tool_guard.py
    class: ToolGuard
    options:
      deny_patterns: ["rm -rf", "dd if="]
```

插件类怎么写，见 [Plugins](/guides/plugins.md)（英文）；参考实现见 [examples/plugins/tool_guard.py](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/examples/plugins/tool_guard.py)（英文）。

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

全局文件 `~/.kohakuterrarium/mcp_servers.yaml` 用的是同一套 schema。见 [MCP](/guides/mcp.md)（英文）。

## 怎么改工具调用格式？

```yaml
tool_format: bracket        # 默认：[/name]@@arg=value\n[name/]
# 或
tool_format: xml            # <name arg="value"></name>
# 或
tool_format: native         # provider-native function calling
```

每种格式的具体样子见 [creatures guide — Tool format](/guides/creatures.md)（英文）；完全自定义分隔符的配置见 [reference/configuration.md — `tool_format`](/reference/configuration.md)（英文）。

## 怎么在 dynamic 和 static skill mode 之间选？

```yaml
skill_mode: dynamic   # 默认；`info` 框架命令按需加载完整文档
# 或
skill_mode: static    # 完整工具文档直接放进 system prompt
```

## 怎么让 creature 在没有用户输入时继续运行？

```yaml
input:
  type: none
triggers:
  - type: timer
    options: { interval: 60 }
    prompt: "Check for anomalies."
```

`none` 输入配任意触发器，就是标准的 monitor-agent 模式。

## 怎么给一次运行设边界？

```yaml
termination:
  max_turns: 15
  max_duration: 600
  idle_timeout: 120
  keywords: ["DONE", "ABORT"]
```

满足任一条件，agent 就会停止。

## 怎么在多个 creature 之间共享状态（不通过 terrarium）？

给它们设同一个 `session_key`：

```yaml
name: writer
session_key: shared-workspace
---
name: reviewer
session_key: shared-workspace
```

这样两个 creature 会共享 `Scratchpad` 和 `ChannelRegistry`。适合多个 creature 在同一进程里运行、但没有 terrarium 的情况。

## 怎么配置 memory/embedding？

```yaml
memory:
  embedding:
    provider: model2vec
    model: "@retrieval"
```

见 [Memory](/guides/memory.md)（英文）。

## 怎么把 creature 固定到某个工作目录？

```bash
kt run path/to/creature --pwd /path/to/project
```

`pwd` 会传给每个工具的 `ToolContext`。

## 排错

- **环境变量没展开。** 要写 `${VAR}`，带花括号。`$VAR` 会按字面量处理。
- **子配置里“丢了”父配置的工具。** 你声明了 `no_inherit: [tools]`。删掉它就会改为扩展。
- **配置能加载，但工具没出现。** 简写名会去内置工具目录里解析，拼错时不会报明显错误。用 `kt info path/to/creature` 检查。
- **两个设置冲突。** CLI 覆盖项（如 `--llm`）优先于配置；配置优先于 `llm_profiles.yaml` 里的 `default_model`。

## 另见

- [configuration](/reference/configuration.md)（英文）：全部字段、类型和默认值。
- [Creatures](/guides/creatures.md)（英文）：目录结构和组成。
- [Plugins](/guides/plugins.md)（英文）、[Custom Modules](/guides/custom-modules.md)（英文）、[MCP](/guides/mcp.md)（英文）、[Memory](/guides/memory.md)（英文）：分别说明对应部分怎么接入。
