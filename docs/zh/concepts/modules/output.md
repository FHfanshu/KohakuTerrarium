# Output

## 它是什么

**output** 模块决定 creature 怎么把东西往外送。controller 产出的内容，不管是 LLM 的文本片段、tool 开始/结束事件、活动通知，还是 token 用量更新，都会先到这里，再被路由到合适的去处。

而且去处不一定只有一个。一个 creature 可以同时往 stdout 打字、往 TTS 流式播报、推到 Discord，再顺手写一份日志。

## 为什么要有它

“把 LLM 的回复打印到 stdout”只是最简单的情况。真部署起来，麻烦马上就来了：

- LLM 流式输出的 chunk，如果有三个监听方，到底往哪发？
- tool 活动要不要混在同一条流里？
- 给用户看的文本和给日志看的文本，能不能走不同出口？
- creature 跑在 web UI 里时，到底是谁在订阅这些事件？

与其每个界面都写一套特判，不如收成一个统一 router，把每个 sink 都当成一个命名 output。

## 怎么定义它

`OutputModule` 是一个异步 consumer，通常会有这些方法：`on_text(chunk)`、`on_tool_start(...)`、`on_tool_complete(...)`、`on_resume(events)`、`start()`、`stop()`。`OutputRouter` 持有一组 output：一个默认 output，再加任意多个 `named_outputs`，然后把事件扇出去。

`controller_direct: true`（默认值）表示 controller 的文本流会直接送到默认 output。`controller_direct: false` 则允许你在中间插一层处理器，比如重写器、安全过滤器、摘要器。

## 怎么实现它

内置 output 有这些：

- **`stdout`** —— 普通终端输出，可配置 prefix、suffix、stream-suffix。
- **`tts`** —— 文本转语音；backend 包括 Fish、Edge、OpenAI，运行时自动选择。
- **`tui`** —— creature 跑在 TUI 里时使用的 Textual 显示层。
- **（隐式）web streaming output** —— creature 跑在 HTTP / WebSocket 服务里时使用。

`OutputRouter`（`modules/output/router.py`）还暴露了一条 activity stream，TUI 和 HTTP 客户端会用它来显示 tool 开始/结束事件，而不是把这些信息硬塞进文本通道。

## 你能拿它做什么

- **安静的 controller，外放的 sub-agent。** 给 sub-agent 配 `output_to: external`，它的文本就会直接流给用户；父 controller 则留在内部。用户看到的是一段完整回复，但实际是专家 sub-agent 写的。
- **按用途分流。** 用户可见答案走 stdout，调试信息走一个写文件的 `logs` named output，最终产物再发到 Discord webhook。
- **后处理文本。** 把 `controller_direct` 设成 `false`，再加一个自定义 output，对 controller 产出的文本做清洗、翻译或加水印。
- **和传输方式解耦。** 同一个 creature 可以跑在 CLI、web 或桌面环境，因为 output 层把传输细节挡住了。

## 别把它看得太死

没有 output 的 creature 也说得通：有些 trigger 只是引发副作用，比如写文件、发邮件。反过来，output 也可以做得很重。一个 Python output 模块完全可以自己再跑个 mini-agent，决定每个 chunk 怎么格式化。听上去有点夸张，实际也确实有点夸张，但不是不行。

## 另见

- [Sub-agent](/zh/concepts/modules/sub-agent.md) —— `output_to: external` 会直接通过 router 往外流。
- [Controller](/zh/concepts/modules/controller.md) —— 真正喂给 router 的是谁。
- [reference/builtins.md — Outputs](/zh/reference/builtins.md) —— 内置列表。
- [guides/custom-modules.md](/zh/guides/custom-modules.md) —— 怎么自己写。