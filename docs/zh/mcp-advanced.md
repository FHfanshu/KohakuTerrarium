# MCP 进阶：它到底是什么，怎么接进 creature

这篇只讲 MCP。

如果你第一次看到这个词，最容易把它误会成两种东西：

- “往 creature 里再注册一类工具”
- “一个能替代 package 的安装机制”

都不是。

在 KohakuTerrarium 里，**MCP 是外部能力接入协议**。你配置的是一个 MCP server 的连接方式，框架作为 client 去连它，再把 server 暴露出来的工具通过一层元工具交给 agent 使用。

---

## 一句话先记住

- **MCP 解决的是：外部工具能力怎么接进来**
- **它不解决：内容怎么安装分发**
- **它也不等于：本地 Python 工具注册**

---

## 在这个项目里，MCP 是怎么工作的

KohakuTerrarium 扮演的是 **MCP client**。

你在配置里声明 MCP server，框架负责：

1. 启动本地 server 进程，或连接远端服务
2. 获取这个 server 暴露的工具列表
3. 把这些工具信息放进 prompt 的 MCP 区域
4. 让模型通过内建的 MCP 元工具去调用它们

项目当前支持两种 transport：

- `stdio`：启动一个本地子进程
- `http`：连接 SSE / 流式 HTTP 服务

这也是为什么现有英文文档会强调：MCP 工具不是一个个直接塞进控制器的工具表里，而是通过元工具桥接出去。

---

## MCP 元工具是什么

连接上 MCP server 之后，模型通常通过这些工具和它交互：

- `mcp_list`
- `mcp_call`
- `mcp_connect`
- `mcp_disconnect`

也就是说，模型不是直接“调用 `sqlite.query` 这个本地工具名”，而是会走类似这种思路：

1. 先知道某个 server 上有哪些工具
2. 需要时调用 `mcp_call`
3. 在参数里指明：
   - `server`
   - `tool`
   - `args`

所以 MCP 更像一层 **工具桥接面**，不是直接给 agent 增加一堆新的本地 builtin。

---

## 最容易混淆的点

### 误解 1：MCP 就是在本地注册工具

不对。

你声明的是 **server 连接方式**，不是“我手写注册一个工具类名”。工具是 server 提供的，不是 creature 本地静态写死的那套 Python tool 定义。

### 误解 2：MCP 可以替代 package

也不对。

- MCP 负责接外部能力
- package 负责分发 creature、tool、plugin、preset 等内容

这两层目标不同。

### 误解 3：接上 MCP 后，工具就和普通 builtin 完全一样

也不完全对。

从“模型能不能调用”这个角度看，它们都属于可调用能力；但从暴露方式看：

- builtin tool：通常是 creature 直接配置的本地工具
- MCP tool：来自已连接 server，通过 `mcp_call` 这层桥接

所以在理解和排错时，还是要分开看。

---

## 什么时候适合优先考虑 MCP

先想你的需求是不是“把外部系统接进来”。

典型场景：

- 访问本地文件系统 MCP
- 接 sqlite / postgres
- 调用 git server
- 访问公司内部知识库
- 接一个远端文档或搜索服务

如果核心问题是“我要用别的系统已经提供好的能力”，优先想 MCP。

如果核心问题是“我要把一整套 creature / plugin / tool 分发给别人复用”，优先想 package，而不是 MCP。

---

## 一个最小示例

```yaml
name: my-mcp-demo
version: "1.0"
base_config: "@kt-defaults/creatures/swe"

tools:
  - info
  - mcp_list
  - mcp_call
  - mcp_connect
  - mcp_disconnect

mcp_servers:
  - name: filesystem
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "."]
```

这个配置说明了三件事：

- `@kt-defaults/creatures/swe` 来自安装后的 package
- `mcp_servers` 声明了一个 MCP server
- 模型通过 MCP 元工具去访问这个 server 暴露的能力

运行：

```bash
kt run ./my-mcp-demo
```

---

## 排错时该先看哪里

如果你怀疑是 MCP 出问题，优先检查这些：

1. server 有没有真的连上
2. `stdio` 命令本身能不能单独跑通
3. `http` 地址是不是 SSE 兼容
4. agent 是否暴露了 `mcp_list` / `mcp_call` 这些元工具
5. tool 明明在 server 上，但是否需要重新连接后才能看到

也就是说，MCP 的排错重点通常是：

- transport
- server 状态
- 元工具是否可用

而不是 package 安没安装。

---

## 推荐继续读什么

- [英文 MCP 指南](../guides/mcp.md)
- [配置文件写法](configuration)
- [内建工具参考](../reference/builtins.md)

---

## 一句话总结

**MCP 解决的是“外部能力怎么接进来”，不是“东西怎么安装”，也不是“本地工具怎么注册”。**
