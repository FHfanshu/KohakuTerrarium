# MCP

给想把 MCP（Model Context Protocol）服务器接到 creature 上的读者。

MCP 是一种客户端—服务器协议，通过 stdio 或 HTTP 暴露工具和其他原语。KohakuTerrarium 充当客户端：你在配置里注册服务器，框架会启动子进程或打开 HTTP 会话，然后通过一组很小的元工具，让 agent 可以调用该服务器的工具。

概念预读：[tool](/concepts/modules/tool.md)（英文）—— MCP 工具本质上就是“工具”，只是以动态方式暴露出来。

## 服务器可以声明在两个地方

### 每个 agent 单独声明

写在 `config.yaml` 里：

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

只有这个 creature 会连接这些服务器。

### 全局声明

写在 `~/.kohakuterrarium/mcp_servers.yaml` 里：

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

也可以用交互方式管理：

```bash
kt config mcp list
kt config mcp add              # 交互式填写 transport、command、args、env、url
kt config mcp edit sqlite
kt config mcp delete sqlite
```

全局服务器可供任何引用它们的 creature 使用。

## Transport

- **stdio** — 启动一个子进程（`command` + `args` + `env`）。适合本地服务器，延迟低，而且每个 agent 的进程生命周期彼此隔离。
- **http** — 打开指向 `url` 的 SSE/流式 HTTP 会话。适合共享服务器或远程服务器，也方便多个 creature 共用同一个服务端。

本地 MCP 服务器，比如 sqlite、filesystem、git，通常选 stdio；托管型服务一般选 http。

## MCP 工具怎么暴露给 LLM

服务器连上后，KohakuTerrarium 会通过**元工具**暴露它的工具：

- `mcp_list` — 列出所有已连接服务器上可用的 MCP 工具。
- `mcp_call` — 按名称调用某个 MCP 工具，并传入参数。
- `mcp_connect` / `mcp_disconnect` — 在运行时管理连接。

系统提示词里会出现一个 “Available MCP Tools” 小节，列出每台服务器的工具（名称和一行描述）。之后，LLM 通过 `mcp_call`，带上 `server`、`tool` 和 `args` 来发起调用。默认的 bracket 格式如下：

```
[/mcp_call]
@@server=sqlite
@@tool=query
@@args={"sql": "SELECT 1"}
[mcp_call/]
```

如果你更喜欢，也可以通过 [`tool_format`](/guides/creatures.md)（英文）切到 `xml` 或 `native`；语义不变。

你不需要把每个 MCP 工具一个个单独接线。用元工具，controller 的工具列表会短很多。

## 列出已连接的服务器

查看某个 agent 的连接情况：

```bash
kt mcp list --agent path/to/creature
```

输出包含名称、transport、command、URL、args 和 env 键名。

## 编程方式使用

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

agent 运行时底层用的就是这套接口。

## 排错

- **服务器连不上（stdio）。** 先跑 `kt config mcp list`，看解析后的命令是什么。再直接在 shell 里试一次，比如 `mcp-server-sqlite /path/to/db`，确认服务器会输出握手信息。
- **服务器连不上（http）。** 确认 URL 支持 SSE。有些服务器同时提供 `/sse` 和 `/ws`；KohakuTerrarium 用的是 SSE。
- **找不到工具。** 元工具列表是在建立连接时算出来的。如果服务器在运行中热添加了工具，重新连接一次（`mcp_disconnect` + `mcp_connect`）。
- **环境变量没替换。** MCP 配置支持 `${VAR}` 和 `${VAR:default}`，和 creature 配置一致。
- **服务器在会话中途崩掉。** stdio 服务器会在下一次 `mcp_call` 时重启。也要看看服务器自己的日志。

## 另见

- [Configuration](/guides/configuration.md)（英文）— `mcp_servers:` 字段。
- [Reference / CLI](/reference/cli.md)（英文）— `kt config mcp`、`kt mcp list`。
- [Concepts / tool](/concepts/modules/tool.md)（英文）— 为什么 MCP 工具不会被特殊对待。
