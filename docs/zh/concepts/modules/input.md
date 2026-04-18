# Input

## 它是什么

**input** 模块是外部世界把活交给 creature 的入口。在那套标准推导里，它位于 controller 前面，负责发出第一个事件。真到实现里看，它其实就是一种特定的 trigger，只不过按约定把它叫作“用户输入”。

## 为什么要有它

如果一个 creature 只响应环境里的 trigger，比如 timer、channel 或 webhook，那你就没法直接跟它聊天。大多数 agent 至少有些时候一头连着人；既然有人，就得有个地方能把输入送进去。

## 怎么定义它

`InputModule` 只需要实现一个异步方法 `get_input()`。这个方法会阻塞，直到有一个 `TriggerEvent` 准备好。它返回什么，系统就把什么推入事件队列，和 timer 触发、channel 收到消息没区别。

所以文档总说“input 也是 trigger”。从结构上讲，确实就是。区别主要在生命周期和意图：input 多半跑在前台，trigger 多半跑在后台；input 带的是用户内容。

## 怎么实现它

内置 input 模块有这些：

- **`cli`** —— 基于 `prompt_toolkit` 的行编辑器，支持历史记录、slash command、多行和粘贴。
- **`tui`** —— creature 跑在 Textual 里时，TUI composer 就是 input。
- **`whisper`** —— 本地麦克风 + Silero VAD + OpenAI Whisper；把 ASR 事件作为 `user_input` 发出来。
- **`asr`** —— 自定义语音识别模块的抽象基类。
- **`none`** —— 一个永远不产出事件的桩模块，给纯 trigger 驱动的 creature 用。

自定义 input 可以在 creature 配置里用 `type: custom` 或 `type: package` 注册。它们必须实现 `InputModule`，由 `bootstrap/io.py` 加载。

## 你能拿它做什么

- **纯 trigger creature。** 用 `input: { type: none }`，再配一个或多个 trigger。比如 cron creature、channel watcher、webhook receiver。
- **多入口聊天。** HTTP 部署不一定需要 CLI input。`AgentSession` 的传输层可以直接用 `inject_input()` 以编程方式塞用户内容。
- **传感器式输入。** 接文件系统 watcher、Discord listener 或 MQTT consumer 都行。对 creature 来说，差别不大。
- **把 input 当策略层。** input 模块可以在内容到达 controller 之前先处理一遍，比如翻译、审核，或者去掉敏感信息。

## 别把它当铁律

input 不是必需的。一个 Discord bot creature，如果根本没有“坐在终端前的人”，完全可以不配 input，只靠 HTTP WebSocket trigger 驱动。反过来也一样，一个 creature 可以同时有几个实际的输入面：用户在 CLI 里打字，webhook 往里推事件，旁边 timer 也在触发。

## 另见

- [Trigger](/zh/concepts/modules/trigger.md) —— 更一般的情况；input 只是其中一种。
- [reference/builtins.md — Inputs](/zh/reference/builtins.md) —— 内置 input 模块完整列表。
- [guides/custom-modules.md](/zh/guides/custom-modules.md) —— 怎么自己写 input。