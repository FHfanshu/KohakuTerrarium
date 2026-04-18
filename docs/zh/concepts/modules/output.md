# Output（输出）

## 它是什么

**Output** 模块负责把 creature 的内容送回外部世界。它接收 controller 发出的所有事件——LLM 的文本分块、工具开始/完成事件、活动通知、token 使用量更新——再把它们分发到对应的输出端。

输出端可以不止一个。一个 creature 可以同时打印到 stdout、推流到 TTS、发到 Discord，再写一份日志到文件里。

## 为什么需要它

“把 LLM 的回复打印到 stdout”只是最简单的情况。真正在部署时，问题会多得多：

- LLM 的流式文本分块在有三个监听方时该发到哪里？
- 工具活动怎么办？走同一条流，还是另一条？
- 给用户看的文本和写日志的文本，要不要共用一个输出端？
- 如果 creature 跑在 Web UI 里，谁在订阅这些事件？

框架没有为每种界面分别写一套特例，而是用一个统一路由器，把每个输出端都当成一个有名字的 output。

## 我们怎么定义它

`OutputModule` 是一个异步消费者，提供 `on_text(chunk)`、`on_tool_start(...)`、`on_tool_complete(...)`、`on_resume(events)`、`start()`、`stop()` 这类方法。`OutputRouter` 持有一组这类模块——一个默认输出，加上任意数量的 `named_outputs`——并负责把事件分发出去。

`controller_direct: true`（默认值）表示 controller 的文本流会直接进入默认输出。设成 `controller_direct: false` 后，你可以在中间插一个处理器，比如改写器、安全过滤器或摘要器。

## 我们怎么实现它

内置输出包括：

- **`stdout`** —— 普通终端输出，可配置 prefix、suffix 和 stream-suffix。
- **`tts`** —— 文本转语音；后端包括 Fish、Edge、OpenAI，运行时自动选择。
- **`tui`** —— creature 在 TUI 下运行时使用的、基于 Textual 的显示层。
- **（隐式）web streaming output** —— creature 运行在 HTTP/WebSocket 服务器中时使用。

`OutputRouter`（`modules/output/router.py`）还提供一条 activity 流，TUI 和 HTTP 客户端可以用它显示工具开始/完成事件，不必把这些事件塞进文本通道。

## 所以你能怎么用

- **安静的 controller，流式输出的 sub-agent。** 给 sub-agent 标上 `output_to: external`，它的文本就会直接流给用户，而父级 controller 留在内部。用户看到的是一段完整回复，但这段回复实际由某个专门 agent 产出。
- **按用途分开输出端。** 给用户看的答案发到 stdout，把调试笔记发到名为 `logs` 的 output 并写入文件，把最终产物发到 Discord webhook。
- **后处理文本。** 把 `controller_direct` 设为 `false`，再加一个自定义 output，在 controller 的文本到达用户之前先做清洗、翻译或加水印。
- **与传输方式解耦。** 同一个 creature 可以跑在 CLI、Web 或桌面环境里，因为输出层把传输细节隔开了。

## 别把它想死了

没有 output 的 creature 也是成立的：有些 trigger 只会产生副作用，比如写文件、发邮件。反过来，output 也不只是个薄封装，它本身就是完整模块——一个 Python 模块完全可以在里面再跑一个 mini-agent，决定每个文本分块该怎么格式化。听上去有点过头，通常也确实没这个必要，但框架允许你这么做。

## 另见

- [Sub-agent](/docs/concepts/modules/sub-agent.md)（英文）—— `output_to: external` 会通过 router 直接把内容流出去。
- [Controller](/docs/concepts/modules/controller.md)（英文）—— 真正向 router 喂数据的是它。
- [reference/builtins.md — Outputs](/docs/reference/builtins.md)（英文）—— 内置输出列表。
- [guides/custom-modules.md](/docs/guides/custom-modules.md)（英文）—— 如何自己写一个。
