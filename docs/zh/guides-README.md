# 使用指南

这一组文档，主要是写给真要上手用 KohakuTerrarium 的人看的：不管你是想把它跑起来、拿它做东西，还是想往里扩展功能，这里都算是比较实用的入口。

如果你现在最需要的是先把整个东西的脑回路搞明白，建议去看 [Concepts](../concepts/README.md)。
如果你要查特别具体的字段、参数、命令选项或者函数签名，那就直接去 [Reference](../reference/README.md)。
如果你更想有人带着你先走一遍、边做边熟悉，那就去 [Tutorials](../tutorials/README.md)。

## 建议先从这里看

- [Getting Started](getting-started.md) —— 从安装开始，教你怎么认证、怎么跑起第一个 creature、怎么接着上次进度继续、怎么打开网页界面。
- [Creatures](creatures.md) —— 讲 creature 本身到底是怎么组成的，包括结构、继承、提示词文件、工具和子代理怎么接线、最后怎么打包。
- [Sessions](sessions.md) —— 讲 `.kohakutr` 文件是干嘛的，怎么恢复会话，还有 compaction 这类整理操作是啥意思。

## 搭建和配置

- [Configuration](configuration.md) —— 如果你的问题是“这个 X 到底该怎么配”，这一篇基本就是按这种实际问题来写的。
- [Creatures](creatures.md) —— 教你怎么写独立可用的 agent。
- [Plugins](plugins.md) —— 讲提示词插件和生命周期插件怎么用。
- [Custom Modules](custom-modules.md) —— 想自己写工具、输入、输出、触发器、子代理，就看这个。
- [MCP](mcp.md) —— 讲怎么给单个 agent 或全局注册 MCP 服务器。
- [Packages](packages.md) —— 讲 `kohaku.yaml` 清单文件、安装模式，还有怎么发布。

## 多代理和组合玩法

- [Terrariums](terrariums.md) —— 讲 channel、根代理、热插拔、observer 这些东西分别是干嘛的。
- [Composition](composition.md) —— 讲怎么在 Python 里用 `>>`、`&`、`|`、`*` 这些方式把流程串起来。
- [Programmatic Usage](programmatic-usage.md) —— 如果你想直接在代码里嵌入 `Agent`、`AgentSession`、`TerrariumRuntime`、`KohakuManager`，看这篇就对了。

## 存起来，以及怎么搜

- [Sessions](sessions.md) —— 主要讲持久化模型，还有怎么恢复之前的运行状态。
- [Memory](memory.md) —— 讲 embedding 提供器、全文检索（FTS）、向量搜索，以及 `search_memory` 这个工具怎么用。

## 把它跑在某个地方

- [Serving](serving.md) —— 讲 `kt web`、`kt app`，还有 `kt serve` 这个守护进程分别怎么用。
- [Frontend Layout](frontend-layout.md) —— 讲网页控制台的面板布局和预设。

## 通过代码学

- [Examples](examples.md) —— 带你看 `examples/` 目录下面每个文件夹分别演示了什么。

## 还有这些也值得看

- [Concepts](../concepts/README.md) —— 想知道为什么它会设计成这样，就去这。
- [Reference](../reference/README.md) —— 当字典查，最全。
- [Development](../dev/README.md) —— 如果你是想参与这个框架本身的开发，就看这里。
