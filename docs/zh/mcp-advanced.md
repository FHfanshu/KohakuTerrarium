# MCP 进阶

MCP 是 Model Context Protocol。在 KohakuTerrarium 里，它是外部能力接入协议——你声明 server 连接方式，框架作为 client 去连接，再把 server 暴露的工具通过元工具交给 agent。

## 它不是什么

不是本地工具注册。不是 package 安装机制。你配置的是 server，工具由 server 提供，不是 creature 本地写死的 Python 定义。

## 怎么工作

KT 是 MCP client。你声明 server，框架：

1. 启动本地进程或连接远端服务
2. 获取工具列表
3. 放进 prompt 的 MCP 区域
4. 模型通过元工具调用

两种 transport：
- `stdio`：本地子进程
- `http`：SSE / 流式 HTTP

## 元工具

连上 server 后，模型用这些：
- `mcp_list`
- `mcp_call`
- `mcp_connect`
- `mcp_disconnect`

不是直接调用 `sqlite.query`，而是先知道 server 上有什么，再用 `mcp_call(server, tool, args)`。

## 常见误解

**MCP 能替代 package？** 不能。MCP 接外部能力，package 分发内容。两件事。

**MCP 工具等于本地 builtin？** 不完全。都能调用，但暴露方式不同：builtin 是 creature 直接配的本地工具，MCP 工具来自 server，通过 `mcp_call` 桥接。

## 什么时候用 MCP

需求是"接外部系统"：
- 文件系统 MCP
- sqlite / postgres
- git server
- 公司知识库
- 远端文档/搜索服务

需求是"分发 creature给别人"：用 package，不是 MCP。

## 示例

```yaml
name: my-mcp-demo
version: "1.0"
base_config: "@kt-defaults/creatures/swe"

tools:
  - info
  - mcp_list
  - mcp_call

mcp_servers:
  - name: filesystem
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "."]
```

跑：
```bash
kt run ./my-mcp-demo
```

## 排错

MCP 出问题时先查：
- server 有没有连上
- stdio 命令能不能单独跑
- http 地址是否 SSE 兼容
- 元工具是否暴露

不是查 package 有没有装。

## 参考

- [英文 MCP 指南](../guides/mcp.md)
- [配置写法](configuration)
- [内建工具参考](../reference/builtins.md)