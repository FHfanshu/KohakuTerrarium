# MCP

给想把 MCP（Model Context Protocol）服务器接到 creature 上的人看。

MCP 是一种客户端—服务器协议，可以通过 stdio 或 HTTP 暴露工具，以及别的协议原语。KohakuTerrarium 在这里是客户端：你在配置里登记服务器，框架会拉起子进程，或者打开 HTTP 会话；接着，agent 就能通过几种很少的元工具去调用服务器提供的工具。

先补一个概念：[tool](../concepts/modules/tool.md)。MCP 工具本质上还是 tool，只是它们是动态挂进来的。

## 服务器可以写在哪

### 每个 agent 单独写

放在 `config.yaml` 里：

```yaml
mcp_servers:
  - name: sqlite
    transport: stdio
    command: mcp-server-sqlite
    args: ["/var/db/my.db"]
  - name: docs_api
    transport: http
    url: https://mcp.example.com/sse
    env:
      API_KEY: "${DOCS_API_KEY}"
```

这样只有这个 creature 会连这些服务器。

### 全局写法

放在 `~/.kohakuterrarium/mcp_servers.yaml` 里：

```yaml
- name: sqlite
  transport: stdio
  command: mcp-server-sqlite
  args: ["/var/db/my.db"]

- name: filesystem
  transport: stdio
  command: npx
  args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/me/projects"]
```

也可以直接用交互命令管理：

```bash
kt config mcp list
kt config mcp add              # 交互式填写 transport、command、args、env、url
kt config mcp edit sqlite
kt config mcp delete sqlite
```

全局服务器可以被任何引用它们的 creature 使用。

## Transport

- **stdio** — 启动一个子进程（`command` + `args` + `env`）。适合本地服务器，延迟低，而且每个 agent 的进程生命周期彼此隔开。
- **http** — 打开一个连到 `url` 的 SSE / 流式 HTTP 会话。适合共享服务或远程服务，也方便多个 creature 共用同一个服务端。

本地 MCP 服务器，比如 sqlite、filesystem、git，一般用 stdio。托管在远端的，通常用 http。

## MCP 工具怎么到 LLM 手里

服务器连上以后，KohakuTerrarium 会通过**元工具**把它的工具暴露出来：

- `mcp_list` — 列出所有已连接服务器上的 MCP 工具。
- `mcp_call` — 按名字调用某个 MCP 工具，并传入参数。
- `mcp_connect` / `mcp_disconnect` — 在运行时管理连接。

系统提示词里会多出一个 “Available MCP Tools” 小节，列出每台服务器的工具，包括名字和一行说明。之后，LLM 就通过 `mcp_call`，带上 `server`、`tool` 和 `args` 来调用。默认的 bracket 格式长这样：

```
[/mcp_call]
@@server=sqlite
@@tool=query
@@args={"sql": "SELECT 1"}
[mcp_call/]
```

如果你更习惯，也可以在 [`tool_format`](creatures.md) 里切到 `xml` 或 `native`，意思不变。

你不用把每个 MCP 工具都单独接一遍。用元工具，controller 的工具列表会短很多。

## 查看已连接的服务器

想看某个 agent 当前连了什么：

```bash
kt mcp list --agent path/to/creature
```

输出会包含名称、transport、command、URL、args 和 env 键名。

## 代码里怎么用

```python
from kohakuterrarium.mcp import MCPClientManager, MCPServerConfig

manager = MCPClientManager()
await manager.connect(MCPServerConfig(
    name="sqlite",
    transport="stdio",
    command="mcp-server-sqlite",
    args=["/tmp/db.sqlite"],
))

tools = await manager.list_tools("sqlite")
result = await manager.call_tool("sqlite", "query", {"sql": "SELECT 1"})
await manager.disconnect("sqlite")
```

agent 运行时，底下用的也是这一套。

## 排错

- **服务器连不上（stdio）。** 先跑 `kt config mcp list`，看看解析出来的命令是什么。再去 shell 里直接试一次，比如 `mcp-server-sqlite /path/to/db`，确认服务器会输出握手信息。
- **服务器连不上（http）。** 确认这个 URL 支持 SSE。有些服务器同时提供 `/sse` 和 `/ws`；KohakuTerrarium 用的是 SSE。
- **找不到工具。** 元工具列表是在连接建立时算出来的。如果服务器运行中热添加了工具，重新连一次就行（`mcp_disconnect` + `mcp_connect`）。
- **环境变量没替换。** MCP 配置支持 `${VAR}` 和 `${VAR:default}`，和 creature 配置一样。
- **服务器在会话中途崩了。** stdio 服务器会在下一次 `mcp_call` 时重新拉起。也别忘了看服务器自己的日志。

## 另见

- [Configuration](configuration.md) — `mcp_servers:` 字段。
- [Reference / CLI](../reference/cli.md) — `kt config mcp`、`kt mcp list`。
- [Concepts / tool](../concepts/modules/tool.md) — 为什么 MCP 工具不会被特殊对待。
