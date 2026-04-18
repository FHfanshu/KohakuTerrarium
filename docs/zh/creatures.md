# Creatures

给想自己写、改，或者打包一个独立 agent 的人看。

**creature** 就是一个自带全套东西的 agent：有自己的 controller、tools、sub-agents、triggers、prompts，还有输入输出。它可以单独跑（`kt run path/to/creature`），可以继承别的 creature，也可以放进 package 里发出去。它自己并不知道自己是不是在 terrarium 里。

先补概念： [what is an agent](../concepts/foundations/what-is-an-agent.md)、[composing an agent](../concepts/foundations/composing-an-agent.md)、[module index](../concepts/modules/README.md)。

## 结构

一个 creature 就是一整个文件夹：

```
creatures/my-agent/
  config.yaml            # 必需
  prompts/
    system.md            # 给 system_prompt_file 用
    context.md           # 给 prompt_context_files 用
  tools/                 # 可选，自定义 tool 模块
  subagents/             # 可选，自定义子 agent 配置
  memory/                # 可选，文本 / markdown memory 文件
```

配置文件查找顺序是：`config.yaml` → `config.yml` → `config.json` → `config.toml`。YAML 里任何地方都能用环境变量插值（`${VAR}` 或 `${VAR:default}`）。

### 最小配置

```yaml
name: my-agent
controller:
  llm: claude-opus-4.6
system_prompt_file: prompts/system.md
tools:
  - read
  - write
  - bash
```

每个字段都对应 `AgentConfig` 里的一个 dataclass 字段。按事情来查，看 [Configuration](configuration.md)；完整字段去 [reference/configuration](../reference/configuration.md)。

## 继承

拿现成 creature 当底子：

```yaml
name: my-swe
base_config: "@kt-defaults/creatures/swe"
controller:
  reasoning_effort: high
tools:
  - name: my_tool          # 新 tool，会追加进去
    type: custom
    module: ./tools/my_tool.py
```

规则就这一套，所有字段都按它来：

- **标量**：子配置覆盖父配置。
- **字典**（`controller`、`input`、`output`、`memory`、`compact` 等）：浅合并。
- **按标识键处理的列表**（`tools`、`subagents`、`plugins`、`mcp_servers`、`triggers`）：按 `name` 合并。名字撞了就以**子项为准**，直接在原位置替换父项。没有 `name` 的项就直接拼接。
- **Prompt 文件**：`system_prompt_file` 会沿继承链拼起来；内联的 `system_prompt` 最后再追加。
- `base_config` 可以解析 `@pkg/...`、`creatures/<name>`（会一路向上找项目根目录），或者相对路径。

有两个开关可以不走默认继承规则：

```yaml
# 1. 整个继承字段不要了，然后你自己从头重写
no_inherit: [tools, plugins]
tools:
  - { name: think, type: builtin }

# 2. 把继承来的 prompt 链整条换掉（等价于
#    no_inherit: [system_prompt, system_prompt_file])
prompt_mode: replace
system_prompt_file: prompts/brand_new.md
```

### 什么时候用 `prompt_mode: replace`

这个对 **sub-agent** 和 **terrarium creature** 特别有用。它们可能继承的是同一个基础人格，但你现在要的说话方式已经完全不是一回事了：

```yaml
# creature 配置里的一个 sub-agent 条目
subagents:
  - name: niche_responder
    base_config: "@kt-defaults/subagents/response"
    prompt_mode: replace
    system_prompt_file: prompts/niche_persona.md
```

```yaml
# terrarium 里的 creature，把一个开箱即用 creature 改造成团队里的专职角色
creatures:
  - name: reviewer
    base_config: "@kt-defaults/creatures/critic"
    prompt_mode: replace
    system_prompt: |
      You are the team's lead reviewer. Speak only to approve or reject, with one-line reasoning.
```

默认值是 `prompt_mode: concat`。如果父 prompt 更像一份通用约定，你只是想在上面加东西，不是彻底换掉，那就用默认的。

### 覆盖列表项，还是扩展列表项？

只要 `name` 撞上，子项就赢：

```yaml
base_config: "@kt-defaults/creatures/general"
tools:
  - { name: bash, type: custom, module: ./tools/safe_bash.py, class: SafeBash }
```

这里子配置里的 `bash` 会直接替换父配置里的 `bash`；其他继承来的 tool 还在。

## Prompt 文件

system prompt 最好放 Markdown 里。里面只写*人格和规则*就够了。工具列表、调用语法、完整 tool 文档，系统会自己聚合进去。

```markdown
<!-- prompts/system.md -->
You are a focused SWE agent. Use tools immediately rather than narrating.
Prefer minimal diffs. Validate before declaring done.
```

模板变量来自 `prompt_context_files`：

```yaml
prompt_context_files:
  style_guide: prompts/style.md
  today:       memory/today.md
```

在 `system.md` 里这样用：

```
## Style guide
{{ style_guide }}

## Today
{{ today }}
```

聚合器会自动加上 tool-list、framework hints、环境信息，还有 `CLAUDE.md`。这些别自己再写一遍，不然就是重复。

## Skill mode：dynamic 还是 static

- `skill_mode: dynamic`（默认）—— prompt 里只放 tool 的一句话说明。controller 需要时再用 `info` 框架命令按需加载完整文档。
- `skill_mode: static` —— 所有 tool 文档一开始就内联进去，system prompt 会更大，但少几次来回。

一般用 `dynamic` 就行。除非你想要一份固定、可审计的 prompt。

## Tool format

这个决定 LLM 调用 tool 时吐出的语法长什么样，也决定框架命令用什么格式。解析器和 system prompt 里的 framework-hints 块都会跟着它走。

下面是 `bash` 调用 `command=ls` 的实际样子：

- `bracket`（默认）—— 用 `[/name]` 开头，`[name/]` 结尾，参数写成 `@@key=value`：
  ```
  [/bash]
  @@command=ls
  [bash/]
  ```
- `xml` —— 普通的标签加属性：
  ```
  <bash command="ls"></bash>
  ```
- `native` —— provider 原生 function calling（OpenAI / Anthropic 的 tool use）。LLM 不会输出文本块，调用信息直接走 API 的结构化字段。
- dict —— 自定义分隔符（见 [configuration reference — `tool_format`](../reference/configuration.md)）。

这三种都能用，挑你的模型更稳的就行。大厂 provider 上 `native` 往往最稳；`bracket` 胜在到处都能跑，本地模型也行。

## Tools 和 sub-agents

```yaml
tools:
  - read                              # 简写，等于 builtin
  - bash
  - name: my_tool                     # custom / package tool
    type: custom
    module: ./tools/my_tool.py
    class_name: MyTool
  - name: web_search
    options:
      max_results: 5
  # 把通用 trigger 暴露成 setup tool，LLM 运行时可以直接调这个名字来安装
  # framework 会用 `CallableTriggerTool` 包一层 trigger 类；简介前面还会加
  # "**Trigger** — "，提醒 LLM 这不是立刻执行一个动作，而是在装一个会长期生效的东西。
  - { name: add_timer, type: trigger }
  - { name: watch_channel, type: trigger }
  - { name: add_schedule, type: trigger }

subagents:
  - worker
  - plan
  - name: my_specialist
    type: custom
    module: ./subagents/specialist.py
    config_name: SPECIALIST_CONFIG
    interactive: true                 # 父 agent 换轮次后它也会继续活着
    can_modify: true
```

能不能在运行时安装 trigger，是按 creature 单独开的。一个 creature 如果没有任何 `type: trigger` 条目，就没法在运行中装 trigger。每个通用 `BaseTrigger` 子类都会自己声明 `setup_tool_name`（比如 `add_timer`）、`setup_description` 和 `setup_param_schema`。你要自己写，去看 [Custom Modules — Triggers](custom-modules.md)。

完整 tool 和 sub-agent 目录见 [reference/builtins](../reference/builtins.md)；自己写则看 [Custom Modules](custom-modules.md)。

## Triggers

```yaml
triggers:
  - type: timer
    options: { interval: 600 }
    prompt: "Health check: anything pending?"
  - type: channel
    options: { channel: alerts }
  - type: custom
    module: ./triggers/webhook.py
    class_name: WebhookTrigger
```

内置类型有：`timer`、`idle`、`webhook`、`channel`、`custom`、`package`。见 [concepts/modules/trigger](../concepts/modules/trigger.md)。

## Startup trigger

creature 启动时会触发一次：

```yaml
startup_trigger:
  prompt: "Review the project status and plan today's work."
```

## 终止条件

```yaml
termination:
  max_turns: 20
  max_duration: 300          # 秒
  idle_timeout: 60           # 多久没事件就算 idle，单位秒
  keywords: ["DONE", "SHUTDOWN"]
```

只要任意一个条件满足，agent 就会停。`keywords` 是在 controller 输出里做子串匹配。

## Session key

多个 creature 可以通过设置同一个 `session_key` 来共用一个 `Session`（scratchpad + channels）：

```yaml
session_key: shared_workspace
```

默认值是 creature 的 `name`。如果在 terrarium 里，每个 creature 会拿到自己的私有 `Session`，同时共享一个 `Environment`。见 [concepts/modules/session-and-environment](../concepts/modules/session-and-environment.md)。

## Framework commands

controller 也可以直接输出和 framework 对话的内联指令，不用走一轮 tool 调用。它们会写在 framework-hints 这个 prompt 块里。

这些框架命令和 tool 调用用的是同一套语法，也就是你配置的 `tool_format`（bracket、XML、native）。默认 bracket 形式下，大概是这样，占位符直接写名字：

- `[/info]tool_or_subagent[info/]` —— 按需加载完整文档。
- `[/read_job]job_id[read_job/]` —— 读取后台任务输出（body 里还能带 `--lines N` 和 `--offset M`）。
- `[/jobs][jobs/]` —— 列出正在跑的任务和它们的 ID。
- `[/wait]job_id[wait/]` —— 阻塞当前轮次，等后台任务结束。

这些命令和 tool 名字共用一个命名空间，所以读后台任务输出的命令特地叫 `read_job`，就是为了不跟读文件的 `read` tool 撞名。

agent 靠这些能力来读流式 tool 输出、查它没记住的文档，以及和自己的后台任务同步。

## User commands

这是*用户*在 CLI / TUI 输入框里敲的 slash 命令。内置的有：

| Command | Alias | Effect |
|---|---|---|
| `/help` | `/h`, `/?` | 列出命令 |
| `/status` | `/info` | 模型、消息、tools、jobs、compact 状态 |
| `/clear` | | 清空对话 |
| `/model [name]` | `/llm` | 列出或切换 LLM profile |
| `/compact` | | 手动 compact |
| `/regen` | `/regenerate` | 重跑上一轮 assistant 输出 |
| `/plugin [list\|enable\|disable\|toggle] [name]` | `/plugins` | 管理 lifecycle plugins |
| `/exit` | `/quit`, `/q` | 正常退出 |

自定义 user command 放在 `builtins/user_commands/` 下，或者跟着 package 一起发。怎么写见 [Custom Modules](custom-modules.md)。

## 输入和输出

```yaml
input:
  type: cli                  # 也可以是：tui, whisper, asr, none, custom, package
  prompt: "> "
  history_file: ~/.my_agent_history

output:
  type: stdout               # 也可以是：tts, tui, custom, package
  named_outputs:
    discord:
      type: custom
      module: ./outputs/discord.py
      class_name: DiscordOutput
      options: { webhook_url: "${DISCORD_WEBHOOK}" }
```

`named_outputs` 能让 tool 或 sub-agent 把内容发到指定出口，比如 Discord webhook、TTS、文件。见 [concepts/modules/output](../concepts/modules/output.md)。

## 每个 creature 自己的 MCP servers

```yaml
mcp_servers:
  - name: sqlite
    transport: stdio
    command: mcp-server-sqlite
    args: ["/var/db/my.db"]
  - name: docs_api
    transport: http
    url: https://mcp.example.com/sse
```

MCP tools 会通过元工具 `mcp_list`、`mcp_call` 暴露给 controller。完整流程看 [MCP](mcp.md)。

## Compaction

```yaml
compact:
  enabled: true
  threshold: 0.8             # 上下文占到 max_tokens 的 80% 就触发
  target: 0.5                # 压到 50% 左右
  keep_recent_turns: 5
  compact_model: gpt-4o-mini  # 总结这一步单独换便宜模型
```

Compaction 在后台跑，不会卡住 controller。见 [Sessions](sessions.md) 和 [concepts/modules/memory-and-compaction](../concepts/modules/memory-and-compaction.md)。

## Plugins

只给这个 creature 挂 lifecycle / prompt plugins：

```yaml
plugins:
  - name: tool_timer
    type: custom
    module: ./plugins/tool_timer.py
    class: ToolTimer
  - name: project_rules
    type: package             # 来自已安装 package 的 manifest
```

见 [Plugins](plugins.md)。

## 打包 creature 复用

把你的 creature 文件夹包进一个 package：

```
my-creatures/
  kohaku.yaml
  creatures/
    my-agent/
      config.yaml
      prompts/...
```

`kohaku.yaml`：

```yaml
name: my-creatures
version: "0.1.0"
description: "My shared creatures"
creatures:
  - name: my-agent
```

本地安装（editable）或者发到 git：

```bash
kt install ./my-creatures -e
# then:
kt run @my-creatures/creatures/my-agent
```

把仓库推到 git 之后，别人就可以直接 `kt install <url>`。完整流程看 [Packages](packages.md)。

## 排错

- **Agent 不按 tool 调用语法来。** 先看 `tool_format`。如果你设成了 `native`，底层 provider 也得支持才行。
- **System prompt 里出现两份 tool 列表。** 你自己在 `system.md` 里又写了一份。删掉，聚合器会自动加。
- **继承来的 creature 把别的都覆盖掉了。** 对标量字段来说这就是预期行为。想保住父级列表，就别在子级重新声明整列。
- **`base_config: "@pkg/..."` 解析失败。** 用 `kt list` 确认 package 已经装上了；package 引用都在 `~/.kohakuterrarium/packages/` 下面。

## 另见

- [Configuration](configuration.md) —— 按任务分类的配置做法。
- [Custom Modules](custom-modules.md) —— 自己写 tools / inputs / outputs / triggers / sub-agents。