# 参考

这一组文档就是给你查东西用的。

你要是已经知道自己要干嘛，只差命令、接口、类、字段或者 hook 的准确信息，就直接看这里。

如果你想先搞懂整体思路，看[概念](../concepts/README.md)。如果你是按任务找做法，看[指南](../guides-README.md)。

## 页面

- [CLI](cli.md) — `kt` 的全部命令和参数。
- [HTTP 和 WebSocket API](http.md) — 所有 REST 路由、WebSocket 端点，以及 Pydantic schema。
- [Python API](python.md) — 所有公开类、函数和 protocol。
- [配置](configuration.md) — creature 配置、terrarium 配置、LLM profile、MCP 目录和包清单里的全部字段。
- [内置项](builtins.md) — 自带的全部工具、sub-agent、input、output、用户命令、框架命令、LLM provider 和 LLM preset。
- [插件 hooks](plugin-hooks.md) — 所有生命周期、LLM、工具、sub-agent、回调和 prompt hook，包括签名和触发时机。

## 这里放什么

参考文档就做一件事：把东西说清楚，别扯远。

- 命令语法
- API 端点
- Python 类和入口点
- 配置字段和接口约定

其他内容不放这里：

- 教程会从头带你走一遍
- 指南是按事情讲做法
- 概念文档讲这套东西为什么这么设计
- 开发文档讲怎么参与这个框架本身的开发
