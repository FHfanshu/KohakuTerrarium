# Creatures

写、定制或打包独立 agent。

creature 是自包含 agent：自己的 controller、tools、sub-agents、triggers、prompts、I/O。可单独跑（`kt run path/to/creature`）、继承另一个 creature、或打包进 package。它不知道自己在 terrarium 里。

概念：[什么是 agent](../concepts/foundations/what-is-an-agent.md)、[组合 agent](../concepts/foundations/composing-an-agent.md)、[模块索引](../concepts/modules/README.md)。

## 结构

creature 在文件夹里：

```
creatures/my-agent/
  config.yaml            # 必须
  prompts/
    system.md            # system_prompt_file 引用
    context.md           # prompt_context_files 引用
  tools/                 # 可选自定义 tool 模块
  subagents/             # 可选自定义 sub-agent 配置
  memory/                # 可选 text/markdown memory 文件
```

查找顺序：`config.yaml` → `config.yml` → `config.json` → `config.toml`。环境变量插值（`${VAR}` 或 `${VAR:default}`）在 YAML 任意位置有效。

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

每个字段对应 `AgentConfig` dataclass。见[配置](configuration.md)任务索引和[配置参考](../reference/configuration.md)完整字段。

## 继承

复用已有 creature 作为基座：

```yaml
name: my-swe
base_config: "@kt-defaults/creatures/swe"
controller:
  reasoning_effort: high
tools:
  - name: my_tool          # 新 tool，追加
    type: custom
    module: ./tools/my_tool.py
```

规则 — 所有字段统一模型：

- **标量**：子覆盖。
- **Dict**（`controller`、`input`、`output`、`memory`、`compact` 等）：浅合并。
- **按名键列表**（`tools`、`subagents`、`plugins`、`mcp_servers`、`triggers`）：按 `name` 合并。同名时**子覆盖**并替换基座条目。无 `name` 的条目拼接。
- **Prompt 文件**：`system_prompt_file` 沿链拼接；inline `system_prompt` 最后追加。
- `base_config` 解析 `@pkg/...`、`creatures/<name>`（向上找项目根）或相对路径。

两个指令退出默认：

```yaml
# 1. 丢弃继承字段，重定义
no_inherit: [tools, plugins]
tools:
  - { name: think, type: builtin }

# 2. 替换继承 prompt 链（等同于 no_inherit: [system_prompt, system_prompt_file]）
prompt_mode: replace
system_prompt_file: prompts/brand_new.md
```

### 什么时候用 prompt_mode: replace

**sub-agent** 和 **terrarium creature** 继承基座 persona 但需要完全不同语气时有用：

```yaml
# creature 配置里的 sub-agent 条目
subagents:
  - name: niche_responder
    base_config: "@kt-defaults/subagents/response"
    prompt_mode: replace
    system_prompt_file: prompts/niche_persona.md
```

```yaml
# terrarium creature 把 OOTB creature 改成团队专家
creatures:
  - name: reviewer
    base_config: "@kt-defaults/creatures/critic"
    prompt_mode: replace
    system_prompt: |
      你是团队主审。只说批准或拒绝，一行理由。
```

默认 `prompt_mode: concat` 适用于基座 prompt 是你要扩展的通用约定，而不是替换。

### 覆盖 vs 扩展列表条目

按 `name` 冲突时子的条目覆盖：

```yaml
base_config: "@kt-defaults/creatures/general"
tools:
  - { name: bash, type: custom, module: ./tools/safe_bash.py, class: SafeBash }
```

子的 `bash` 替换基座的 `bash`，位置不变；其他继承 tools 保留。

## Prompt 文件

系统提示词放在 Markdown。只放 *personality 和 guideline* — tool 列表、调用语法、完整 tool 文档自动聚合。

```markdown
<!-- prompts/system.md -->
你是专注的 SWE agent。直接用工具，不要叙述。
偏好最小 diff。做完前验证。
```

模板变量来自 `prompt_context_files`：

```yaml
prompt_context_files:
  style_guide: prompts/style.md
  today:       memory/today.md
```

在 `system.md` 里：

```
## Style guide
{{ style_guide }}

## Today
{{ today }}
```

聚合器自动追加 tool-list、framework hints、env info、`CLAUDE.md`。不要重复。

## Skill mode：dynamic vs static

- `skill_mode: dynamic`（默认） — tools 在 prompt 里显示为一行描述。controller 用 `info` framework command 按需加载完整文档。
- `skill_mode: static` — 所有 tool 文档 upfront inline（更大的系统提示词，少往返）。

除非要固定可审计 prompt，用 `dynamic`。

## Tool format

控制 LLM 发出 tool 调用的语法（以及 framework command）。作用于 parser 和系统提示词的 framework-hints block。

`bash` 调用 `command=ls` 的具体例子：

- `bracket`（默认） — `[/name]` 开，`[name/]` 关，args 用 `@@key=value` 行：
  ```
  [/bash]
  @@command=ls
  [bash/]
  ```
- `xml` — 标签带属性：
  ```
  <bash command="ls"></bash>
  ```
- `native` — 供应商原生 function calling（OpenAI / Anthropic tool use）。LLM 不发文本块；API 结构化携带调用。
- dict — 自定义分隔符（见[配置参考 — tool_format](../reference/configuration.md)）。

三种格式互换 — 选模型处理最好的。`native` 在主要供应商上最可靠；`bracket` 在所有模型包括本地模型都能用。

## Tools 和 sub-agents

```yaml
tools:
  - read                              # 简写 = builtin
  - bash
  - name: my_tool                     # custom / package tool
    type: custom
    module: ./tools/my_tool.py
    class_name: MyTool
  - name: web_search
    options:
      max_results: 5
  # 把 universal trigger 当 setup tool — LLM 运行时安装
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
    interactive: true                 # 跨 parent turn 存活
    can_modify: true
```

可 setup 的 triggers per-creature opt-in — 没有 `type: trigger` 条目的 creature 不能运行时安装 trigger。每个 `BaseTrigger` 子类声明自己的 `setup_tool_name`（如 `add_timer`）、`setup_description`、`setup_param_schema`。写自己的见[自定义模块 — Triggers](custom-modules.md)。

见[内建参考](../reference/builtins.md)完整 tool/sub-agent 目录；[自定义模块](custom-modules.md)写自己的。

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

内建类型：`timer`、`idle`、`webhook`、`channel`、`custom`、`package`。见[概念/modules/trigger](../concepts/modules/trigger.md)。

## Startup trigger

creature 启动时触发一次：

```yaml
startup_trigger:
  prompt: "Review the project status and plan today's work."
```

## Termination conditions

```yaml
termination:
  max_turns: 20
  max_duration: 300          # 秒
  idle_timeout: 60           # 无事件秒数
  keywords: ["DONE", "SHUTDOWN"]
```

任一条件满足停止 agent。`keywords` 是 controller 输出的子串匹配。

## Session key

多个 creature 可共享同一个 `Session`（scratchpad + channels）：

```yaml
session_key: shared_workspace
```

默认是 creature 的 `name`。在 terrarium 里，每个 creature 有私有 `Session` 和共享 `Environment`；见[概念/modules/session-and-environment](/concepts/modules/session-and-environment.md)（英文）。and-environment.md)。t.md)。