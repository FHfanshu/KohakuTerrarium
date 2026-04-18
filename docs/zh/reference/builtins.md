# 内建项

KohakuTerrarium 自带的全部内建工具、子代理、输入、输出、用户命令、框架命令、LLM 提供方和 LLM 预设。

想了解工具和子代理各自的形态，见[工具](/concepts/modules/tool.md)（英文）和[子代理](/concepts/modules/sub-agent.md)（英文）。
按任务查用法，见[creatures](/guides/creatures.md)（英文）和[custom modules](/guides/custom-modules.md)（英文）。

## Tools

内建工具类位于 `src/kohakuterrarium/builtins/tools/`。
在 creature 配置里，把它们的裸名写到 `tools:` 下即可注册。

### Shell 与脚本

**`bash`** — 运行 shell 命令。会在 `bash`、`zsh`、`sh`、`fish`、`pwsh` 中选择第一个可用项。遵循 `KT_SHELL_PATH`。捕获 stdout 和 stderr，超出上限会截断。直接执行。

- 参数：`command`（str）、`working_dir`（str，可选）、`timeout`（float，可选）。

**`python`** — 运行 Python 子进程。遵循 `working_dir` 和 `timeout`。直接执行。

- 参数：`code`（str）、`working_dir`、`timeout`。

### 文件操作

**`read`** — 读取文本、图片或 PDF 内容。会按文件记录读取状态。图片返回为 `base64` data URL。PDF 支持需要 `pymupdf`。直接执行。

- 参数：`path`（str）、`offset`（int，可选）、`limit`（int，可选）。

**`write`** — 创建或覆盖文件。会创建父目录。若文件此前没有先读过，则禁止覆盖，除非设置了 `new`。直接执行。

- 参数：`path`、`content`、`new`（bool，可选）。

**`edit`** — 自动识别 unified diff（`@@`）或 search/replace 形式。拒绝处理二进制文件。直接执行。

- 参数：`path`、`old_text`/`new_text` 或 `diff`、`replace_all`（bool）。

**`multi_edit`** — 对单个文件按顺序应用一组编辑。以文件为单位原子提交。模式：`strict`（每一条编辑都必须成功）、`best_effort`（跳过失败项）、默认模式（部分应用并给出报告）。直接执行。

- 参数：`path`、`edits: list[{old, new}]`、`mode`。

**`glob`** — 按 mtime 排序的 glob。遵循 `.gitignore`。支持提前终止。直接执行。

- 参数：`pattern`、`root`（可选）、`limit`（可选）。

**`grep`** — 跨文件做正则搜索。支持 `ignore_case`。跳过二进制文件。直接执行。

- 参数：`pattern`、`path`（可选）、`ignore_case`（bool）、`max_matches`。

**`tree`** — 目录列表；对 markdown 文件会附带 YAML frontmatter 摘要。直接执行。

- 参数：`path`、`depth`。

### 结构化数据

**`json_read`** — 按 dot-path 读取 JSON 文档。直接执行。

- 参数：`path`、`query`（dot-path）。

**`json_write`** — 在 dot-path 处赋值。需要时会创建嵌套对象。直接执行。

- 参数：`path`、`query`、`value`。

### Web

**`web_fetch`** — 把 URL 拉取为 markdown。尝试顺序是 `crawl4ai` → `trafilatura` → Jina proxy → `httpx + html2text`。上限 100k 字符，超时 30 秒。直接执行。

- 参数：`url`。

**`web_search`** — 使用 DuckDuckGo 搜索，返回 markdown 格式结果。直接执行。

- 参数：`query`、`max_results`（int）、`region`（str）。

### 交互与记忆

**`ask_user`** — 通过 stdin 向用户提问（仅 CLI 或 TUI）。有状态。

- 参数：`question`。

**`think`** — 空操作；把推理保存为工具事件，写入事件日志。直接执行。

- 参数：`thought`。

**`scratchpad`** — 会话级 KV 存储。会话中的代理共享同一份数据。

- 参数：`action`（`get` | `set` | `delete` | `list`）、`key`、`value`。

**`search_memory`** — 对当前会话已索引事件做 FTS / 语义 / 自动搜索。支持按代理过滤。

- 参数：`query`、`mode`（`auto`/`fts`/`semantic`/`hybrid`）、`k`、`agent`。

### 通信

**`send_message`** — 向某个通道发消息。先解析 creature 本地通道，再解析环境共享通道。直接执行。

- 参数：`channel`、`content`、`sender`（可选）。

### 自省

**`info`** — 按需加载任意工具或子代理的文档。会委托到 `src/kohakuterrarium/builtin_skills/` 下的 skill manifest，以及每个代理自己的覆盖配置。直接执行。

- 参数：`target`（工具名或子代理名）。

**`stop_task`** — 按 id 取消正在运行的后台任务或 trigger。直接执行。

- 参数：`job_id`（任意工具调用返回的 job id，或 `add_timer`/`watch_channel`/`add_schedule` 返回的 trigger id）。

### 可安装的触发器（通过 `type: trigger` 作为工具暴露）

每个通用 trigger 类都会通过 `modules/trigger/callable.py:CallableTriggerTool` 包装成独立工具。creature 通过把 trigger 的 `setup_tool_name` 写到 `tools:` 下并指定 `type: trigger` 来启用它。工具描述会加上前缀 `**Trigger** — `，让 LLM 知道调用它会安装一个长期存在的副作用。三者都会立即返回已安装的 trigger id；trigger 本身在后台运行。

**`add_timer`**（包装 `TimerTrigger`）— 安装一个周期性定时器。

- 参数：`interval`（秒，必填）、`prompt`（必填）、`immediate`（bool，默认 false）。

**`watch_channel`**（包装 `ChannelTrigger`）— 监听指定名称的通道。

- 参数：`channel_name`（必填）、`prompt`（可选，支持 `{content}`）、`filter_sender`（可选）。
- 代理自身名称会自动写入 `ignore_sender`，避免触发自己。

**`add_schedule`**（包装 `SchedulerTrigger`）— 按时钟对齐执行的计划任务。

- 参数：`prompt`（必填）；`every_minutes`、`daily_at`（HH:MM）、`hourly_at`（0-59）三者必须且只能填一个。

### Terrarium（仅 root）

**`terrarium_create`** — 启动一个新的 terrarium 实例。仅 root 可用。

**`terrarium_send`** — 向 root 所在 terrarium 的某个通道发送消息。

**`creature_start`** — 运行时热插入一个 creature。

**`creature_stop`** — 运行时停止一个 creature。

---

## Sub-agents

内置子代理配置位于 `src/kohakuterrarium/builtins/subagents/`。
在 creature 配置中，把它们的名字写到 `subagents:` 下即可引用。

| 名称 | Tools | 用途 |
|---|---|---|
| `worker` | `read`, `write`, `bash`, `glob`, `grep`, `edit`, `multi_edit` | 修 bug、重构、跑验证。 |
| `coordinator` | `send_message`, `scratchpad` | 拆解 → 分发 → 汇总。 |
| `explore` | `glob`, `grep`, `read`, `tree`, `bash` | 只读探索。 |
| `plan` | `explore` 的工具 + `think` | 只读规划。 |
| `research` | `web_search`, `web_fetch`, `read`, `write`, `think`, `scratchpad` | 外部资料调研。 |
| `critic` | `read`, `glob`, `grep`, `tree`, `bash` | 代码审查。 |
| `response` | `read` | 面向用户的文案生成。通常配 `output_to: external`。 |
| `memory_read` | 在 memory 文件夹上使用 `tree`、`read`、`grep` | 从代理记忆中取回内容。 |
| `memory_write` | `tree`, `read`, `write` | 把发现写入记忆。 |
| `summarize` | （无工具） | 为交接或重置压缩对话。 |

---

## Inputs

内建输入模块位于 `src/kohakuterrarium/builtins/inputs/`。

**`cli`** — stdin 提示输入。选项：`prompt`、`exit_commands`。

**`none`** — 不接收输入。用于仅靠 trigger 运行的代理。

**`whisper`** — 麦克风 + Silero VAD + `openai-whisper`。选项包括 `model`、`language` 和 VAD 阈值。需要 FFmpeg。

**`asr`** — 自定义语音识别的抽象基类。

还有两类输入会在运行时动态解析：

- `tui` — 在 TUI 模式下由 Textual 应用挂载。
- `custom` / `package` — 通过 `module` + `class_name` 字段加载。

---

## Outputs

内建输出模块位于 `src/kohakuterrarium/builtins/outputs/`。

**`stdout`** — 输出到 stdout。选项：`prefix`、`suffix`、`stream_suffix`、`flush_on_stream`。

**`tts`** — Fish / Edge / OpenAI TTS（自动检测）。支持流式输出和硬中断。

另外还有几类路由型输出：

- `tui` — 渲染到 Textual TUI 的组件树中。
- `custom` / `package` — 通过 module + class 加载。

---

## User commands

可在输入模块中使用的 slash 命令。位于 `src/kohakuterrarium/builtins/user_commands/`。

| 命令 | 别名 | 用途 |
|---|---|---|
| `/help` | `/h`, `/?` | 列出命令。 |
| `/status` | `/info` | 显示模型、消息数、工具、任务、compact 状态。 |
| `/clear` | | 清空对话（会话日志仍保留历史）。 |
| `/model [name]` | `/llm` | 显示当前模型，或切换 profile。 |
| `/compact` | | 手动压缩上下文。 |
| `/regen` | `/regenerate` | 重新执行上一轮 assistant 输出。 |
| `/plugin [list\|enable\|disable\|toggle] [name]` | `/plugins` | 查看或切换插件。 |
| `/exit` | `/quit`, `/q` | 正常退出。Web 端可能需要 force 标志。 |

---

## Framework commands

LLM 可以直接发出的内联指令，用来替代工具调用。它们直接和框架通信，不走工具往返。定义位于 `src/kohakuterrarium/commands/`。

框架命令和工具调用使用**同一套语法家族**——遵循 creature 配置的 `tool_format`（bracket / XML / native）。默认的 bracket 形式如下，使用裸标识符占位：

- `[/info]tool_or_subagent[info/]` — 按需加载某个工具或子代理的完整文档。
- `[/read_job]job_id[read_job/]` — 读取后台任务输出。正文里支持 `--lines N` 和 `--offset M`。
- `[/jobs][jobs/]` — 列出正在运行的任务及其 ID。
- `[/wait]job_id[wait/]` — 阻塞当前轮次，直到某个后台任务完成。

命令名与工具名共享同一命名空间；读取任务输出的命令叫 `read_job`，用来避开和文件读取工具 `read` 的冲突。定义位于 `src/kohakuterrarium/commands/`。

---

## LLM providers

内建 provider 类型（后端）：

| Provider | Transport | 说明 |
|---|---|---|
| `codex` | 通过 Codex OAuth 访问 OpenAI chat API | 使用 ChatGPT 订阅认证；`kt login codex`。 |
| `openai` | OpenAI chat API | API key 认证。 |
| `openrouter` | OpenAI 兼容接口 | API key 认证；可路由到多种模型。 |
| `anthropic` | 原生 Anthropic messages API | 使用专用 client。 |
| `gemini` | Google 提供的 OpenAI 兼容 endpoint | API key 认证。 |
| `mimo` | 小米 MiMo 原生接口 | `kt login mimo`。 |

配置里还会引用一些社区 provider：`together`、`mistral`、`deepseek`、`vllm`、`generic`。规范列表见 `kohakuterrarium.llm.presets`。

## LLM presets

内建在 `src/kohakuterrarium/llm/presets.py` 中。可作为 `llm:` 或 `--llm` 的值使用。括号中是别名。

### OpenAI via Codex OAuth

- `gpt-5.4`（别名：`gpt5`、`gpt54`）
- `gpt-5.3-codex`（`gpt53`）
- `gpt-5.1`
- `gpt-4o`（`gpt4o`）
- `gpt-4o-mini`

### OpenAI direct

- `gpt-5.4-direct`
- `gpt-5.4-mini-direct`
- `gpt-5.4-nano-direct`
- `gpt-5.3-codex-direct`
- `gpt-5.1-direct`
- `gpt-4o-direct`
- `gpt-4o-mini-direct`

### OpenAI via OpenRouter

- `or-gpt-5.4`
- `or-gpt-5.4-mini`
- `or-gpt-5.4-nano`
- `or-gpt-5.3-codex`
- `or-gpt-5.1`
- `or-gpt-4o`
- `or-gpt-4o-mini`

### Anthropic Claude via OpenRouter

- `claude-opus-4.6`（别名：`claude-opus`、`opus`）
- `claude-sonnet-4.6`（别名：`claude`、`claude-sonnet`、`sonnet`）
- `claude-sonnet-4.5`
- `claude-haiku-4.5`（别名：`claude-haiku`、`haiku`）
- `claude-sonnet-4`（旧版）
- `claude-opus-4`（旧版）

### Anthropic Claude direct

- `claude-opus-4.6-direct`
- `claude-sonnet-4.6-direct`
- `claude-haiku-4.5-direct`

### Google Gemini

通过 OpenRouter：

- `gemini-3.1-pro`（别名：`gemini`、`gemini-pro`）
- `gemini-3-flash`（`gemini-flash`）
- `gemini-3.1-flash-lite`（`gemini-lite`）
- `nano-banana`

直连（OpenAI 兼容 endpoint）：

- `gemini-3.1-pro-direct`
- `gemini-3-flash-direct`
- `gemini-3.1-flash-lite-direct`

### Google Gemma（OpenRouter）

- `gemma-4-31b`（别名：`gemma`、`gemma-4`）
- `gemma-4-26b`

### Qwen（OpenRouter）

- `qwen3.5-plus`（`qwen`）
- `qwen3.5-flash`
- `qwen3.5-397b`
- `qwen3.5-27b`
- `qwen3-coder`（`qwen-coder`）
- `qwen3-coder-plus`

### Moonshot Kimi（OpenRouter）

- `kimi-k2.5`（`kimi`）
- `kimi-k2-thinking`

### MiniMax（OpenRouter）

- `minimax-m2.7`（`minimax`）
- `minimax-m2.5`

### Xiaomi MiMo

通过 OpenRouter：

- `mimo-v2-pro`（`mimo`）
- `mimo-v2-flash`

直连：

- `mimo-v2-pro-direct`
- `mimo-v2-flash-direct`

### GLM（Z.ai，经由 OpenRouter）

- `glm-5`（`glm`，默认别名）
- `glm-5-turbo`（`glm`）

### xAI Grok（OpenRouter）

- `grok-4`（`grok`）
- `grok-4.20`
- `grok-4.20-multi`
- `grok-4-fast`（`grok-fast`）
- `grok-4.1-fast`
- `grok-code-fast`（`grok-code`）
- `grok-3`
- `grok-3-mini`

### Mistral（OpenRouter）

- `mistral-large-3`（别名：`mistral`、`mistral-large`）
- `mistral-medium-3.1`（`mistral-medium`）
- `mistral-medium-3`
- `mistral-small-4`（`mistral-small`）
- `mistral-small-3.2`
- `magistral-medium`（`magistral`）
- `magistral-small`
- `codestral`
- `devstral-2`（`devstral`）
- `devstral-medium`
- `devstral-small`
- `pixtral-large`
- `ministral-3-14b`（`ministral`）
- `ministral-3-8b`

内建预设合并时，也会纳入已安装包贡献的 `llm_presets`；见[configuration.md — Package manifest](/reference/configuration.md#package-manifest-kohakuyaml)（英文）。

---

## Prompt plugins

内建 prompt 插件（由 `prompt/aggregator.py` 加载）。按优先级排序，数值越小越早执行。

| Priority | Name | 输出内容 |
|---|---|---|
| 50 | `ToolListPlugin` | 工具名和一行描述。 |
| 45 | `FrameworkHintsPlugin` | 框架命令示例（`info`、`read_job`、`jobs`、`wait`）以及工具调用格式示例。 |
| 40 | `EnvInfoPlugin` | `cwd`、平台、日期时间。 |
| 30 | `ProjectInstructionsPlugin` | 加载 `CLAUDE.md` 和 `.claude/rules.md`。 |

自定义 prompt 插件需要继承 `BasePlugin`，并通过 creature 配置中的 `plugins` 字段注册。生命周期和回调钩子见[plugin-hooks.md](/reference/plugin-hooks.md)（英文）。

---

## Compose algebra

运算符优先级：`* > | > & > >>`。

| 运算符 | 含义 |
|---|---|
| `a >> b` | 顺序执行（自动展平）。`>> {key: fn}` 会形成一个 Router。 |
| `a & b` | 积（`asyncio.gather`；向各分支广播输入）。 |
| `a \| b` | 回退（捕获异常后尝试下一个）。 |
| `a * N` | 重试（额外重试 N 次）。 |

工厂：`Pure`、`Sequence`、`Product`、`Fallback`、`Retry`、`Router`、`Iterator`。包装辅助：`agent(config_path)` 用于持久代理，`factory(config)` 用于每次调用都新建的临时代理。`effects.Effects()` 提供副作用日志句柄。

Runnable 方法：`.map(f)`（后处理输出）、`.contramap(f)`（预处理输入）、`.fails_when(pred)`（谓词为真时抛错）。

---

## MCP surface

内建 MCP 元工具（配置了 `mcp_servers` 时会暴露）：

- `mcp_list` — 列出已连接服务器及其工具。
- `mcp_call` — 调用指定服务器上的某个工具。
- `mcp_connect` — 连接配置中声明的服务器。
- `mcp_disconnect` — 断开连接。

服务器工具会在系统提示中的 `## Available MCP Tools` 下展示。传输方式：`stdio`（子进程）和 `http`/SSE。

Python 接口：`kohakuterrarium.mcp` 中的 `MCPServerConfig`、`MCPClientManager`。

---

## Extensions

包的 `kohaku.yaml` 可以贡献 `creatures`、`terrariums`、`tools`、`plugins`、`llm_presets` 和 `python_dependencies`。可用 `kt extension list` 查看。Python 模块通过 `module:class` 引用解析；配置通过 `@pkg/path` 解析。见[configuration.md — Package manifest](/reference/configuration.md#package-manifest-kohakuyaml)（英文）。

---

## See also

- 概念：[tool](/concepts/modules/tool.md)（英文）、[sub-agent](/concepts/modules/sub-agent.md)（英文）、[channel](/concepts/modules/channel.md)（英文）、[patterns](/concepts/patterns.md)（英文）。
- 指南：[creatures](/guides/creatures.md)（英文）、[custom modules](/guides/custom-modules.md)（英文）、[plugins](/guides/plugins.md)（英文）。
- 参考：[configuration](/reference/configuration.md)（英文）、[plugin-hooks](/reference/plugin-hooks.md)（英文）、[python](/reference/python.md)（英文）、[cli](/reference/cli.md)（英文）。
