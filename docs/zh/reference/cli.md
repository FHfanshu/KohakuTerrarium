# CLI 参考

这里是 `kt` 的完整命令表：命令、子命令、参数都在这。你可以用它来启动 creature、启动 terrarium、管包、配 LLM、开 Web UI、查保存下来的 session。

如果你想先弄明白 creature、terrarium 和 root agent 到底是什么，先看[概念 / 边界](../concepts/boundaries.md)。如果你是来找具体做法的，可以看[快速开始](../guides/getting-started.md)和[creature](../guides/creatures.md)。

## 入口

- `kt` — 安装后的控制台脚本。
- `python -m kohakuterrarium` — 和上面等价。
- 如果启动时没带子命令（比如用 Briefcase 双击打开），`kt` 会直接拉起桌面应用。

## 全局参数

| 参数 | 用途 |
|---|---|
| `--version` | 打印版本、安装来源、包路径、Python 版本和 git commit。 |
| `--verbose` | 和 `--version` 一起用时，还会打印 `$VIRTUAL_ENV`、可执行文件路径和 git 分支。 |

---

## 核心命令

### `kt run`

运行单个 creature。

```
kt run <agent_path> [flags]
```

位置参数：

- `agent_path` — 包含 `config.yaml` 的本地文件夹，或者像 `@kt-biome/creatures/swe` 这样的包引用。

参数：

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--log-level` | `DEBUG\|INFO\|WARNING\|ERROR` | `INFO` | 根 logger 的级别。 |
| `--session` | path | auto | session 文件写到哪里。可以给绝对路径，也可以只写 `~/.kohakuterrarium/sessions/` 下面的名字。 |
| `--no-session` | flag | — | 完全关闭 session 持久化。 |
| `--llm` | str | — | 覆盖 LLM profile，例如 `gpt-5.4`、`claude-opus-4.6`。 |
| `--mode` | `cli\|plain\|tui` | auto | 交互模式。TTY 下默认是 `cli`，否则默认是 `plain`。 |

行为：

- `@package/...` 路径会解析到 `~/.kohakuterrarium/packages/<pkg>/...`，可编辑安装时会跟随 `.link` 指针。
- 不加 `--no-session` 的话，会自动在 `~/.kohakuterrarium/sessions/` 下建一个 `.kohakutr` session。
- 退出时会顺手提示你一条 `kt resume <name>`。
- 按 Ctrl+C 会走优雅关闭流程。

### `kt resume`

恢复之前的 session。它会根据 session 文件自动判断这是 agent 还是 terrarium。

```
kt resume [session] [flags]
```

位置参数：

- `session` — 名称前缀、完整文件名，或者完整路径。不写时，会弹出最近 10 个 session 的交互式选择器。

参数：

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--pwd` | path | session 里保存的 cwd | 覆盖工作目录。 |
| `--last` | flag | — | 不提示，直接恢复最近一个 session。 |
| `--log-level` | 同 `kt run` | | |
| `--mode` | 同 `kt run` | | terrarium session 会强制用 `tui`。 |
| `--llm` | str | | 给恢复的 session 覆盖 LLM profile。 |

行为：

- 支持 `.kohakutr` 和旧的 `.kt` 扩展名，解析时会自动去掉。
- 如果前缀匹配到多个结果，会弹出选择器。

### `kt list`

列出已安装的包和本地 agent。

```
kt list [--path agents]
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--path` | str | `agents` | 除了已安装包，还会额外扫描这个本地目录。 |

### `kt info`

打印 creature 配置里的名称、描述、模型、工具、sub-agent 和文件列表。

```
kt info <agent_path>
```

---

## Terrarium

### `kt terrarium run`

跑一个多 agent terrarium。

```
kt terrarium run <terrarium_path> [flags]
```

位置参数：

- `terrarium_path` — YAML 文件，或者 `@package/terrariums/<name>`。

参数：

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--log-level` | 同 `kt run` | | |
| `--seed` | str | — | 启动时注入到 seed channel 的 prompt。 |
| `--seed-channel` | str | `seed` | 接收 `--seed` 的 channel。 |
| `--observe` | channel 名列表 | — | 要观察的 channel（plain/log 模式下）。 |
| `--no-observe` | flag | — | 完全关闭观察。 |
| `--session` | path | auto | session 文件路径。 |
| `--no-session` | flag | — | 关闭持久化。 |
| `--llm` | str | — | 给所有 creature（以及 root）统一覆盖 LLM profile。 |
| `--mode` | `cli\|plain\|tui` | `tui` | UI 模式。 |

行为：

- `tui` 会开出多个标签页：root、每个 creature、还有每个 channel。
- `cli` 会在 RichCLI 里挂载 root（如果有）；没有 root 就挂第一个 creature。
- `plain` 会把被观察到的 channel 消息直接输出到 stdout。

### `kt terrarium info`

打印 terrarium 的名字、creature、收发哪些 channel，还有 channel 列表。

```
kt terrarium info <terrarium_path>
```

---

## 包管理

### `kt install`

从 git URL 或本地路径安装一个包。

```
kt install <source> [-e|--editable] [--name <name>]
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `-e`, `--editable` | flag | — | 不复制文件，而是写一个指向源码的 `<name>.link`。 |
| `--name` | str | 从 URL/路径推导 | 改掉安装后的包名。 |

`<source>` 可以这样写：

- git URL（会 clone 到 `~/.kohakuterrarium/packages/<name>`）
- 本地目录（直接复制，或者配合 `-e` 建立链接）

### `kt uninstall`

删除已安装的包。

```
kt uninstall <name>
```

### `kt update`

更新基于 git 的包。可编辑安装和非 git 包会跳过。

```
kt update [target] [--all]
```

| 参数 | 类型 | 说明 |
|---|---|---|
| `--all` | flag | 更新所有基于 git 的包。 |

### `kt edit`

用 `$EDITOR` 打开 creature 或 terrarium 的配置文件；如果没设，就依次回退到 `$VISUAL`、`nano`。

```
kt edit <target>
```

`target` 支持包引用（`@pkg/creatures/name`）和本地路径。

---

## 配置：`kt config`

### `kt config show`

列出 CLI 会用到的所有配置文件路径。

### `kt config path`

输出下面这些路径里的某一个：`home`、`llm_profiles`、`api_keys`、`mcp_servers`、`ui_prefs`。

```
kt config path [name]
```

### `kt config edit`

用 `$EDITOR` 打开配置文件。不写名字时，默认打开 `llm_profiles`。

```
kt config edit [name]
```

### `kt config provider`（别名：`kt config backend`）

管 LLM provider（backend）。

#### `kt config provider list`

列出每个 provider 的 Name、Backend Type 和 Base URL。

#### `kt config provider add`

交互式添加。会依次询问 backend 类型（`openai`、`codex`、`anthropic`）、base URL 和 `api_key_env`。

```
kt config provider add [name]
```

#### `kt config provider edit`

和 `add` 一样，但会先带出当前配置。

```
kt config provider edit <name>
```

#### `kt config provider delete`

```
kt config provider delete <name>
```

### `kt config llm`（别名：`kt config model`、`kt config preset`）

管 LLM preset。

#### `kt config llm list`

列出 Name、Provider、Model 和默认标记。

#### `kt config llm show`

把完整 preset 打出来：provider、model、max_context、max_output、base_url、api_key_env、temperature、reasoning_effort、service_tier、extra_body。

```
kt config llm show <name>
```

#### `kt config llm add`

交互式添加。可以顺手把新的 preset 设成默认值。

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

不带参数时打印当前默认值；带 `name` 时就把它设为默认。

```
kt config llm default [name]
```

### `kt config key`

管理保存下来的 API key。

#### `kt config key list`

列：provider、api_key_env、source（`stored`/`env`/`missing`）、掩码后的值。

#### `kt config key set`

把 API key 保存到 `~/.kohakuterrarium/api_keys.yaml`。如果不写 `value`，会进入带掩码的交互输入。

```
kt config key set <provider> [value]
```

#### `kt config key delete`

清除保存的 key（provider 这条记录本身会保留）。

```
kt config key delete <provider>
```

### `kt config login`

`kt login` 的别名。见[认证](#认证)。

### `kt config mcp`

管理全局 MCP 服务器目录（`~/.kohakuterrarium/mcp_servers.yaml`）。

- `list` — 显示文件路径和服务器清单。
- `add [name]` — 交互式添加。会询问传输方式（`stdio`/`http`）、command、args JSON、env JSON、URL。
- `edit <name>` — 交互式编辑。
- `delete <name>` — 删除条目。

---

## 认证

### `kt login`

向某个 provider 认证。

```
kt login <provider>
```

- `codex` backend：使用 OAuth device-code 流程。token 保存在 `~/.kohakuterrarium/codex-auth.json`。
- API key 类型的 backend：会提示输入（带掩码），然后保存到 `~/.kohakuterrarium/api_keys.yaml`。

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

## 记忆与搜索

### `kt embedding`

给一个已保存的 session 建 FTS 和向量索引。

```
kt embedding <session> [--provider ...] [--model ...] [--dimensions N]
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--provider` | `auto\|model2vec\|sentence-transformer\|api` | `auto` | `auto` 优先选 jina-v5-nano。 |
| `--model` | str | 取决于 provider | provider 对应的模型，也支持 `@tiny`、`@best`、`@multilingual-best` 这类别名。 |
| `--dimensions` | int | — | Matryoshka 截断，用更短的向量。 |

### `kt search`

搜索某个 session 的记忆。

```
kt search <session> <query> [flags]
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--mode` | `fts\|semantic\|hybrid\|auto` | `auto` | 搜索模式。有向量就自动选 semantic，没有就选 FTS。 |
| `--agent` | str | — | 只看某个 agent 的事件。 |
| `-k` | int | `10` | 最大返回条数。 |

---

## Web 和桌面 UI

### `kt web`

运行 Web 服务器（阻塞式，单进程）。

```
kt web [flags]
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--host` | str | `127.0.0.1` | 绑定的 host。 |
| `--port` | int | `8001` | 绑定端口。端口占用时会自动递增。 |
| `--dev` | flag | — | 只启 API（前端请单独用 `vite dev` 启动）。 |
| `--log-level` | 同 `kt run` | | |

### `kt app`

运行原生桌面版本（需要 pywebview）。

```
kt app [--port 8001] [--log-level ...]
```

### `kt serve`

管理 Web 服务器守护进程。进程状态保存在 `~/.kohakuterrarium/run/web.{pid,json,log}`。

#### `kt serve start`

启动一个脱离终端的服务器进程。

```
kt serve start [--host 127.0.0.1] [--port 8001] [--dev] [--log-level INFO]
```

#### `kt serve stop`

先发 SIGTERM，超过宽限时间后再发 SIGKILL。

```
kt serve stop [--timeout 5.0]
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--timeout` | float | `5.0` | 等待优雅关闭的秒数。 |

#### `kt serve restart`

先 `stop`，再 `start`，并把所有参数转发给 `start`。

#### `kt serve status`

打印 `running` / `stopped` / `stale`、PID、URL、started_at、version、git commit。

#### `kt serve logs`

读取 `~/.kohakuterrarium/run/web.log`。

```
kt serve logs [--follow] [--lines 80]
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--follow` | flag | — | 持续跟日志。 |
| `--lines` | int | `80` | 一开始先打印多少行。 |

---

## 扩展

### `kt extension list`

列出已安装包带来的全部工具、插件和 LLM preset。可编辑安装会标出来。

### `kt extension info`

显示包的元数据，以及它包含的 creatures、terrariums、tools、plugins 和 LLM presets。

```
kt extension info <name>
```

---

## MCP（按 agent）

### `kt mcp list`

列出某个 agent 的 `config.yaml` 里 `mcp_servers:` 段声明的 MCP 服务器。列包括：name、transport、command、URL、args、env keys。

```
kt mcp list --agent <path>
```

---

## 文件路径

| 路径 | 用途 |
|---|---|
| `~/.kohakuterrarium/` | 主目录。 |
| `~/.kohakuterrarium/llm_profiles.yaml` | LLM preset 和 provider。 |
| `~/.kohakuterrarium/api_keys.yaml` | 保存的 API key。 |
| `~/.kohakuterrarium/mcp_servers.yaml` | 全局 MCP 服务器目录。 |
| `~/.kohakuterrarium/ui_prefs.json` | UI 偏好设置。 |
| `~/.kohakuterrarium/codex-auth.json` | Codex OAuth token。 |
| `~/.kohakuterrarium/sessions/*.kohakutr` | 保存的 session（也兼容旧版 `*.kt`）。 |
| `~/.kohakuterrarium/packages/` | 已安装包（复制件或 `.link` 指针）。 |
| `~/.kohakuterrarium/run/web.{pid,json,log}` | Web 守护进程状态。 |

## 环境变量

| 变量 | 用途 |
|---|---|
| `EDITOR`, `VISUAL` | `kt edit` / `kt config edit` 用的编辑器。 |
| `VIRTUAL_ENV` | `kt --version --verbose` 会显示它。 |
| `<PROVIDER>_API_KEY` | 每个 provider 的 `api_key_env` 指向的环境变量。 |
| `KT_SHELL_PATH` | 覆盖 `bash` 工具使用的 shell。 |
| `KT_SESSION_DIR` | 给 Web API 覆盖 session 目录，默认是 `~/.kohakuterrarium/sessions`。 |

## 退出码

- `0` — 成功。
- `1` — 通用错误。
- 编辑器退出码 — 用于 `kt edit` / `kt config edit`。

## 交互提示

下面这些命令可能会进入交互模式：

- `kt resume` 不带参数，或者前缀有歧义时。
- `kt terrarium run` 在没有 root 且没有 `--seed` 时。
- `kt login`。
- `kt config` 下所有 `... add` 子命令。
- `kt config key set` 不带 value 时。

## 包引用语法

`@<pkg-name>/<path-inside-pkg>` 会解析到 `~/.kohakuterrarium/packages/<pkg-name>/<path-inside-pkg>`，或者跟随 `<pkg-name>.link`。`kt run`、`kt terrarium run`、`kt edit`、`kt update` 和 `kt info` 都支持这种写法。

## Terrarium TUI 斜杠命令

在 `kt terrarium run --mode tui` 里，输入栏支持斜杠命令。内置的有 `/exit`、`/quit`。其他命令来自 terrarium 注册的用户命令。见[内置项中的用户命令](builtins.md#用户命令)。

## 另见

- 概念：[边界](../concepts/boundaries.md)、[session 持久化](../concepts/impl-notes/session-persistence.md)
- 指南：[快速开始](../guides/getting-started.md)、[sessions](../guides/sessions.md)、[terrariums](../guides/terrariums.md)
- 参考：[配置](configuration.md)、[内置项](builtins.md)、[HTTP](http.md)
