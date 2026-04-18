# MCP 进阶

这篇文档面向需要连接 MCP（Model Context Protocol）服务器的用户。

MCP 是一种客户端-服务器协议，通过 stdio 或 HTTP 暴露工具（以及其他能力）。KohakuTerrarium 作为客户端运行：你在配置中注册一个服务器，框架会启动子进程或打开 HTTP 会话，服务器的工具就可以通过一组元工具从智能体中调用了。

概念入门：[工具](../concepts/modules/tool.md) —— MCP 工具"只是工具"，只是动态暴露出来的。

## 在哪里声明 MCP 服务器

### 方式一：在 creature 配置中声明

在 `config.yaml` 里写：

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

这样配置的服务器只有这个 creature 会连接。

### 方式二：全局声明

在 `~/.kohakuterrarium/mcp_servers.yaml` 里写：

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

也可以用命令行交互式管理：

```bash
kt config mcp list
kt config mcp add              # 交互式添加：选择 transport、填写 command、args、env、url
kt config mcp edit sqlite
kt config mcp delete sqlite
```

全局配置的服务器对所有引用它的 creature 都可用。

## 两种传输方式

- **stdio** —— 启动一个子进程（`command` + `args` + `env`）。适合本地服务器，延迟低，每个智能体有独立的进程生命周期。
- **http** —— 打开一个 SSE/流式 HTTP 会话连接到 `url`。适合共享/远程服务器，多个 creature 可以共用同一个服务器。

选择建议：本地 MCP 服务器（sqlite、filesystem、git）用 stdio，托管的服务用 http。

## MCP 工具如何到达 LLM

服务器连接成功后，KohakuTerrarium 通过**元工具**暴露其工具：

- `mcp_list` —— 列出所有已连接服务器上可用的 MCP 工具。
- `mcp_call` —— 按名称调用指定的 MCP 工具并传入参数。
- `mcp_connect` / `mcp_disconnect` —— 运行时连接管理。

系统提示词会包含一个"Available MCP Tools"区块，列出每个服务器的工具（名称 + 一行描述）。然后 LLM 用 `mcp_call` 调用，传入 `server`、`tool` 和 `args`。默认的括号格式是这样：

```
[/mcp_call]
@@server=sqlite
@@tool=query
@@args={"sql": "SELECT 1"}
[mcp_call/]
```

如果你想用 `xml` 或 `native` 格式，可以通过 [`tool_format`](configuration.md) 配置 —— 语义不变。

你不需要为每个 MCP 工具单独配置 —— 元工具的方式让控制器的工具列表保持简洁。

## 查看已连接的服务器

查看指定智能体连接的 MCP 服务器：

```bash
kt mcp list --agent path/to/creature
```

输出包括名称、传输方式、命令、URL、参数、环境变量键名。

## npx 类型 MCP 的配置注意事项

使用 npx 运行 MCP 服务器时，需要注意以下几点：

### 必须加 `-y` 参数

```yaml
mcp_servers:
  - name: filesystem
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allow"]
```

`-y` 参数表示自动确认安装，否则 npx 会等待用户输入确认，导致连接超时。

### 指定允许访问的目录

文件系统 MCP 服务器需要明确指定允许访问的目录：

```yaml
args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/me/projects", "/home/me/documents"]
```

可以指定多个目录，用空格分隔。

### 环境变量传递

如果 MCP 服务器需要环境变量（比如 API key），在 `env` 字段里配置：

```yaml
mcp_servers:
  - name: some-api
    transport: stdio
    command: npx
    args: ["-y", "@example/mcp-server"]
    env:
      API_KEY: "${MY_API_KEY}"      # 从环境变量读取
      ANOTHER_VAR: "${VAR:default}" # 支持默认值
```

### 首次运行会下载包

npx 首次运行某个包时会下载，可能需要几秒钟。建议先在终端手动运行一次确认能正常启动：

```bash
npx -y @modelcontextprotocol/server-filesystem /tmp
```

看到服务器输出握手信息就说明正常。

### 常见的 npx MCP 服务器

| 包名 | 用途 |
|------|------|
| `@modelcontextprotocol/server-filesystem` | 文件系统访问 |
| `@modelcontextprotocol/server-sqlite` | SQLite 数据库操作 |
| `@modelcontextprotocol/server-git` | Git 仓库操作 |
| `@modelcontextprotocol/server-github` | GitHub API |

## 代码中使用

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

智能体的运行时底层就是用这个。

## 排错

- **stdio 服务器连不上**。运行 `kt config mcp list` 查看解析后的命令。在 shell 里手动试一下（`mcp-server-sqlite /path/to/db`），确认服务器能打印握手信息。
- **http 服务器连不上**。确认 URL 支持 SSE。有些服务器同时暴露 `/sse` 和 `/ws` —— KohakuTerrarium 用的是 SSE。
- **工具找不到**。元工具列表在连接时计算。如果服务器热添加了工具，需要重连（`mcp_disconnect` + `mcp_connect`）。
- **环境变量没替换**。MCP 配置支持 `${VAR}` 和 `${VAR:default}`，和 creature 配置一样。
- **会话中途服务器崩溃**。stdio 服务器会在下次 `mcp_call` 时自动重启。检查服务器自己的日志。

## MCP 不是什么

- **不是本地工具注册**。你配置的是 server，工具由 server 提供，不是 creature 本地写死的 Python 定义。
- **不是 package 安装机制**。MCP 接外部能力，package 分发内容。两件事。

## 什么时候用 MCP

需求是"接外部系统"：
- 文件系统 MCP
- sqlite / postgres
- git server
- 公司知识库
- 远端文档/搜索服务

需求是"分发 creature 给别人"：用 package，不是 MCP。

## 参考

- [英文 MCP 指南](../guides/mcp.md)
- [配置写法](configuration)
- [CLI 参考](../reference/cli.md) —— `kt config mcp`、`kt mcp list`
- [工具概念](../concepts/modules/tool.md) —— 为什么 MCP 工具没有被特殊对待