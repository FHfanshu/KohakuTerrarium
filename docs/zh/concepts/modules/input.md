# Input

## 它是什么

**Input** 模块是外部世界把工作交给 creature 的入口。在经典推导里，它位于 controller 之前，负责发出第一个事件。放到实现里看，它其实就是一种特定的 trigger，按约定叫“用户输入”。

## 为什么需要它

如果一个 creature 只响应环境里的 trigger，比如定时器、channel 或 webhook，那你就没法直接和它对话。大多数 agent 的环路里，至少有些时候一端会是人；既然有人，就得有个地方让他输入内容。

## 我们怎么定义它

`InputModule` 只需要实现一个异步方法 `get_input()`。这个方法会阻塞，直到有一个 `TriggerEvent` 可用。它返回什么，系统就会把什么推入事件队列，和定时器触发、channel 消息进入队列时没有区别。

所以文档一直说“input 也是 trigger”。从结构上讲，确实如此。两者主要区别在生命周期和用途：input 通常跑在前台，trigger 通常在后台；input 带的是用户内容。

## 我们怎么实现它

内置 input 模块有：

- **`cli`** — 基于 `prompt_toolkit` 的行编辑器。支持历史记录、斜杠命令、多行输入和粘贴。
- **`tui`** — creature 跑在 Textual 里时，TUI composer 就是 input。
- **`whisper`** — 本地麦克风 + Silero VAD + OpenAI Whisper；把 ASR 事件作为 `user_input` 发出。
- **`asr`** — 自定义语音识别模块的抽象基类。
- **`none`** — 一个永远不会产出事件的桩模块，给纯 trigger 驱动的 creature 用。

自定义 input 可以通过 creature 配置里的 `type: custom` 或 `type: package` 注册。它们必须实现 `InputModule`，并由 `bootstrap/io.py` 加载。

## 所以你能做什么

- **纯 trigger creature。** 用 `input: { type: none }`，再配一个或多个 trigger。比如 cron creature、channel watcher、webhook receiver。
- **多入口聊天。** 如果部署走的是 HTTP，就不一定需要 CLI input。`AgentSession` 的传输层可以通过 `inject_input()` 以编程方式推入用户内容。
- **传感器式输入。** 接一个文件系统 watcher、Discord listener 或 MQTT consumer 都可以。对 creature 来说，这些没有本质区别。
- **把 input 当成策略层。** input 模块可以在内容到达 controller 之前先做处理，比如翻译、审核，或者去掉敏感信息。

## 不要被它限制

input 不是必需的。一个 Discord bot creature，如果没有“坐在终端前的人”，完全可以不配 input，只靠 HTTP WebSocket trigger 驱动。反过来也一样，一个 creature 可以同时有几个实际上的输入面：用户在 CLI 里输入，webhook 往里推事件，旁边还有定时器在触发。

## 另见

- [Trigger](/concepts/modules/trigger.md)（英文）— 更一般的情况；input 只是其中一种。
- [reference/builtins.md — Inputs](/reference/builtins.md)（英文）— 内置 input 模块完整列表。
- [guides/custom-modules.md](/guides/custom-modules.md)（英文）— 如何自己写 input。
