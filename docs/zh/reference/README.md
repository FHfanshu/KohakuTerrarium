# 参考

参考页是拿来查具体信息的。

如果你已经知道自己要做什么，只是想找准确的命令、接口、类、字段或 hook，就看这里。

如果你想先搞懂整体思路，看[概念](../concepts/README.md)。如果你是按任务找做法，看[指南](../guides/README.md)。

## 页面

- [CLI](cli.md) — `kt` 的全部命令和参数。
- [HTTP 和 WebSocket API](http.md) — 所有 REST 路由、WebSocket 端点，以及 Pydantic schema。
- [Python API](python.md) — 所有公开类、函数和 protocol。
- [配置](configuration.md) — creature 配置、terrarium 配置、LLM profile、MCP 目录和包清单里的全部字段。
- [内置项](builtins.md) — 自带的全部工具、sub-agent、input、output、用户命令、框架命令、LLM provider 和 LLM preset。
- [插件 hooks](plugin-hooks.md) — 所有生命周期、LLM、工具、sub-agent、回调和 prompt hook，包括签名和触发时机。

## 这里放什么

参考文档只管一件事：写得准，范围小。

- 命令语法
- API 端点
- Python 类和入口点
- 配置字段和接口约定

其他内容不放这里：

- 教程带你从头走一遍
- 指南告诉你怎么完成某件事
- 概念文档解释系统为什么这么设计
- 开发文档讲怎么参与框架本身的开发
