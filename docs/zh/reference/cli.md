# CLI 参考

`kt` 的全部命令、子命令和 flag。CLI 是框架的操作入口：启动 creature、启动 terrarium、管理包、配置 LLM、运行 Web UI，以及搜索已保存的 session。

想先弄清 creature、terrarium 和 root agent 之间的关系，见[概念：boundaries](/concepts/boundaries.md)（英文）。如果你是按任务来查，见[入门指南](/guides/getting-started.md)（英文）和[creatures 指南](/guides/creatures.md)（英文）。

## 入口

- `kt` — 安装后的控制台脚本。
- `python -m kohakuterrarium` — 等价写法。
- 不带子命令调用时（例如通过 Briefcase 双击启动），`kt` 会自动打开桌面应用。

## 全局 flags

| Flag | 用途 |
|---|---|
| `--version` | 输出版本号、安装来源、包路径、Python 版本和 git commit。 |
| `--verbose` | 与 `--version` 一起使用时，还会输出 `$VIRTUAL_ENV`、可执行文件路径和 git branch。 |

---

## 核心命令

### `kt run`

运行单个 creature。

```
kt run <agent_path> [flags]
```

位置参数：

- `agent_path` — 包含 `config.yaml` 的本地目录，或类似 `@kt-defaults/creatures/swe` 的包引用。

Flags：

| Flag | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--log-level` | `DEBUG\|INFO\|WARNING\|ERROR` | `INFO` | root logger 的级别。 |
| `--session` | path | auto | 要写入的 session 文件；可以是绝对路径，也可以是 `~/.kohakuterrarium/sessions/` 下的名称。 |
| `--no-session` | flag | — | 完全关闭 session 持久化。 |
| `--llm` | str | — | 覆盖 LLM profile，例如 `gpt-5.4`、`claude-opus-4.6`。 |
| `--mode` | `cli\|plain\|tui` | auto | 交互模式。在 TTY 中默认是 `cli`，否则默认是 `plain`。 |

行为：

- `@package/...` 路径会解析到 `~/.kohakuterrarium/packages/<pkg>/...`，可编辑安装时会跟随 `.link` 指针。
- 除非设置了 `--no-session`，否则会在 `~/.kohakuterrarium/sessions/` 下自动创建扩展名为 `.kohakutr` 的 session。
- 退出时会打印 `kt resume <name>` 提示。
- 按 Ctrl+C 会触发优雅退出。

### `kt resume`

恢复之前的 session。是 agent 还是 terrarium，会根据 session 文件自动判断。

```
kt resume [session] [flags]
```

位置参数：

- `session` — 名称前缀、完整文件名，或完整路径。不填时会打开一个交互式选择器，显示最近 10 个 session。

Flags：

| Flag | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--pwd` | path | session 中保存的 cwd | 覆盖工作目录。 |
| `--last` | flag | — | 直接恢复最近一次 session，不再提示。 |
| `--log-level` | 同 `kt run` | | |
| `--mode` | 同 `kt run` | | terrarium session 会强制使用 `tui`。 |
| `--llm` | str | | 为恢复的 session 覆盖 LLM profile。 |

行为：

- 接受 `.kohakutr` 和旧版 `.kt` 扩展名，并会自动去掉扩展名处理。
- 如果前缀匹配到多个结果，会弹出选择器。

### `kt list`

列出已安装的包和本地 agent。

```
kt list [--path agents]
```

| Flag | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--path` | str | `agents` | 除已安装包外，额外扫描的本地目录。 |

### `kt info`

输出 creature 配置的名称、描述、模型、工具、sub-agent 和文件。

```
kt info <agent_path>
```

---

## Terrarium

### `kt terrarium run`

运行一个多 agent terrarium。

```
kt terrarium run <terrarium_path> [flags]
```

位置参数：

- `terrarium_path` — YAML 文件，或 `@package/terrariums/<name>`。

Flags：

| Flag | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--log-level` | 同 `kt run` | | |
| `--seed` | str | — | 启动时注入到 seed channel 的 prompt。 |
| `--seed-channel` | str | `seed` | 接收 `--seed` 的 channel。 |
| `--observe` | channel 名列表 | — | 要观察的 channel（plain/log 模式）。 |
| `--no-observe` | flag | — | 完全关闭观察。 |
| `--session` | path | auto | session 文件路径。 |
| `--no-session` | flag | — | 关闭持久化。 |
| `--llm` | str | — | 为*每个* creature（以及 root）覆盖 LLM profile。 |
| `--mode` | `cli\|plain\|tui` | `tui` | UI 模式。 |

行为：

- `tui` 会挂载多标签视图：root + 每个 creature + 每个 channel。
- `cli` 会在 RichCLI 中挂载 root（如果有），否则挂载第一个 creature。
- `plain` 会把被观察 channel 的消息流式输出到 stdout。

### `kt terrarium info`

输出 terrarium 的名称、creature、listen/send channel 和 channel 列表。

```
kt terrarium info <terrarium_path>
```

---

## 包管理

### `kt install`

从 git URL 或本地路径安装包。

```
kt install <source> [-e|--editable] [--name <name>]
```

| Flag | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `-e`, `--editable` | flag | — | 不复制文件，而是写入一个指向源目录的 `<name>.link`。 |
| `--name` | str | 从 URL/路径推导 | 覆盖安装后的包名。 |

`<source>` 可以是：

- git URL（会克隆到 `~/.kohakuterrarium/packages/<name>`）。
- 本地目录（直接复制，或使用 `-e` 建立链接）。

### `kt uninstall`

移除已安装的包。

```
kt uninstall <name>
```

### `kt update`

更新由 git 支持的包。可编辑安装和非 git 包会跳过。

```
kt update [target] [--all]
```

| Flag | 类型 | 说明 |
|---|---|---|
| `--all` | flag | 更新所有由 git 支持的包。 |

### `kt edit`

在 `$EDITOR` 中打开 creature 或 terrarium 配置（若未设置，则依次回退到 `$VISUAL`、`nano`）。

```
kt edit <target>
```

`target` 支持包引用（如 `@pkg/creatures/name`）和本地路径。

---

## 配置：`kt config`

### `kt config show`

输出 CLI 使用的所有配置文件路径。

### `kt config path`

输出以下某一项对应的路径：`home`、`llm_profiles`、`api_keys`、`mcp_servers`、`ui_prefs`。

```
kt config path [name]
```

### `kt config edit`

在 `$EDITOR` 中打开配置文件。不传名称时，默认打开 `llm_profiles`。

```
kt config edit [name]
```

### `kt config provider`（别名：`kt config backend`）

管理 LLM provider（backend）。

#### `kt config provider list`

显示每个 provider 的 Name、Backend Type 和 Base URL。

#### `kt config provider add`

交互式命令。会依次询问 backend type（`openai`、`codex`、`anthropic`）、base URL 和 `api_key_env`。

```
kt config provider add [name]
```

#### `kt config provider edit`

字段与 `add` 相同，但会先用当前条目的值填充。

```
kt config provider edit <name>
```

#### `kt config provider delete`

```
kt config provider delete <name>
```

### `kt config llm`（别名：`kt config model`、`kt config preset`）

管理 LLM preset。

#### `kt config llm list`

显示 Name、Provider、Model，以及 Default 标记。

#### `kt config llm show`

输出完整 preset：provider、model、max_context、max_output、base_url、api_key_env、temperature、reasoning_effort、service_tier、extra_body。

```
kt config llm show <name>
```

#### `kt config llm add`

交互式命令。可选把新 preset 设为默认值。

```
kt config llm add [name]
```

#### `kt config llm edit`

```
kt config llm edit <name>
```

#### `kt config llm delete`

```
kt config llm delete <name>
```

#### `kt config llm default`

不带参数时输出当前默认值；传入 `name` 时则设置默认值。

```
kt config llm default [name]
```

### `kt config key`

管理已保存的 API key。

#### `kt config key list`

列：provider、api_key_env、source（`stored`/`env`/`missing`）和脱敏后的值。

#### `kt config key set`

把 API key 保存到 `~/.kohakuterrarium/api_keys.yaml`。如果省略 `value`，会提示输入（脱敏显示）。

```
kt config key set <provider> [value]
```

#### `kt config key delete`

清除已保存的 key（provider 条目本身会保留）。

```
kt config key delete <provider>
```

### `kt config login`

`kt login` 的别名。见[认证](/reference/cli.md#auth)（英文）。

### `kt config mcp`

管理全局 MCP server catalog（`~/.kohakuterrarium/mcp_servers.yaml`）。

- `list` — 显示文件路径和 server 清单。
- `add [name]` — 交互式命令。会询问 transport（`stdio`/`http`）、command、args JSON、env JSON、URL。
- `edit <name>` — 交互式编辑。
- `delete <name>` — 删除条目。

---

## 认证

### `kt login`

对 provider 进行认证。

```
kt login <provider>
```

- 对 `codex` backend：使用 OAuth device-code 流程。token 保存在 `~/.kohakuterrarium/codex-auth.json`。
- 对 API-key backend：会提示输入（脱敏显示），并保存到 `~/.kohakuterrarium/api_keys.yaml`。

---

## 模型

### `kt model`

这是 `kt config llm` 的一层薄封装：

```
kt model list
kt model default [name]
kt model show <name>
```

---

## Memory 与搜索

### `kt embedding`

为已保存的 session 构建 FTS 和向量索引。

```
kt embedding <session> [--provider ...] [--model ...] [--dimensions N]
```

| Flag | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--provider` | `auto\|model2vec\|sentence-transformer\|api` | `auto` | `auto` 会优先使用 jina-v5-nano。 |
| `--model` | str | 取决于 provider | provider 专用模型，也支持 `@tiny`、`@best`、`@multilingual-best` 这类别名。 |
| `--dimensions` | int | — | Matryoshka 截断（更短的向量）。 |

### `kt search`

搜索 session 的 memory。

```
kt search <session> <query> [flags]
```

| Flag | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--mode` | `fts\|semantic\|hybrid\|auto` | `auto` | 搜索模式。`auto` 会在存在向量时选择 semantic，否则使用 FTS。 |
| `--agent` | str | — | 只搜索某个 agent 的事件。 |
| `-k` | int | `10` | 最大结果数。 |

---

## Web 与桌面 UI

### `kt web`

运行 Web server（阻塞式，单进程）。

```
kt web [flags]
```

| Flag | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--host` | str | `127.0.0.1` | 绑定的 host。 |
| `--port` | int | `8001` | 绑定的端口。若被占用会自动递增。 |
| `--dev` | flag | — | 只启动 API（前端需单独用 `vite dev` 提供）。 |
| `--log-level` | 同 `kt run` | | |

### `kt app`

运行原生桌面构建版本（需要 pywebview）。

```
kt app [--port 8001] [--log-level ...]
```

### `kt serve`

管理 Web server 守护进程。进程状态保存在 `~/.kohakuterrarium/run/web.{pid,json,log}`。

#### `kt serve start`

启动一个脱离终端的 server 进程。

```
kt serve start [--host 127.0.0.1] [--port 8001] [--dev] [--log-level INFO]
```

#### `kt serve stop`

先发送 SIGTERM，宽限期后再发送 SIGKILL。

```
kt serve stop [--timeout 5.0]
```

| Flag | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--timeout` | float | `5.0` | 等待优雅退出的秒数。 |

#### `kt serve restart`

先 `stop` 再 `start`，并把所有 flags 转发给 `start`。

#### `kt serve status`

输出 `running` / `stopped` / `stale`、PID、URL、started_at、version、git commit。

#### `kt serve logs`

读取 `~/.kohakuterrarium/run/web.log`。

```
kt serve logs [--follow] [--lines 80]
```

| Flag | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--follow` | flag | — | 持续追踪日志。 |
| `--lines` | int | `80` | 初始输出的行数。 |

---

## 扩展

### `kt extension list`

列出已安装包提供的全部 tool、plugin 和 LLM preset。可编辑安装会单独标记。

### `kt extension info`

显示包元数据，以及它提供的 creatures、terrariums、tools、plugins 和 LLM presets。

```
kt extension info <name>
```

---

## MCP（按 agent）

### `kt mcp list`

列出 agent 的 `config.yaml` 中 `mcp_servers:` 段声明的 MCP server。列包括：name、transport、command、URL、args、env keys。

```
kt mcp list --agent <path>
```

---

## 文件路径

| 路径 | 用途 |
|---|---|
| `~/.kohakuterrarium/` | Home。 |
| `~/.kohakuterrarium/llm_profiles.yaml` | LLM presets 和 providers。 |
| `~/.kohakuterrarium/api_keys.yaml` | 已保存的 API keys。 |
| `~/.kohakuterrarium/mcp_servers.yaml` | 全局 MCP server catalog。 |
| `~/.kohakuterrarium/ui_prefs.json` | UI 偏好设置。 |
| `~/.kohakuterrarium/codex-auth.json` | Codex OAuth tokens。 |
| `~/.kohakuterrarium/sessions/*.kohakutr` | 已保存的 sessions（也接受旧版 `*.kt`）。 |
| `~/.kohakuterrarium/packages/` | 已安装包（复制文件或 `.link` 指针）。 |
| `~/.kohakuterrarium/run/web.{pid,json,log}` | Web 守护进程状态。 |

## 环境变量

| 变量 | 用途 |
|---|---|
| `EDITOR`, `VISUAL` | `kt edit` / `kt config edit` 使用的编辑器。 |
| `VIRTUAL_ENV` | `kt --version --verbose` 会输出它。 |
| `<PROVIDER>_API_KEY` | 每个 provider 的 `api_key_env` 所引用的环境变量。 |
| `KT_SHELL_PATH` | 覆盖 `bash` tool 使用的 shell。 |
| `KT_SESSION_DIR` | 覆盖 Web API 使用的 session 目录（默认 `~/.kohakuterrarium/sessions`）。 |

## 退出码

- `0` — 成功。
- `1` — 通用错误。
- 编辑器退出码 — 用于 `kt edit` / `kt config edit`。

## 交互式提示

这些命令可能会进入交互式提示：

- `kt resume` 不带参数，或名称前缀有歧义时。
- `kt terrarium run` 在没有 root 且没有 `--seed` 时。
- `kt login`。
- `kt config` 下所有 `... add` 子命令。
- 不带 value 的 `kt config key set`。

## 包引用语法

`@<pkg-name>/<path-inside-pkg>` 会解析到 `~/.kohakuterrarium/packages/<pkg-name>/<path-inside-pkg>`，或者跟随 `<pkg-name>.link`。`kt run`、`kt terrarium run`、`kt edit`、`kt update` 和 `kt info` 都接受这种写法。

## Terrarium TUI 斜杠命令

在 `kt terrarium run --mode tui` 中，输入栏支持斜杠命令。内建命令有：`/exit`、`/quit`。额外命令来自 terrarium 注册的 user commands。见[内建：user commands](/reference/builtins.md#user-commands)（英文）。

## 另见

- 概念：[boundaries](/concepts/boundaries.md)（英文）、[session persistence](/concepts/impl-notes/session-persistence.md)（英文）。
- 指南：[getting-started](/guides/getting-started.md)（英文）、[sessions](/guides/sessions.md)（英文）、[terrariums](/guides/terrariums.md)（英文）。
- 参考：[configuration](/reference/configuration.md)（英文）、[builtins](/reference/builtins.md)（英文）、[http](/reference/http.md)（英文）。
