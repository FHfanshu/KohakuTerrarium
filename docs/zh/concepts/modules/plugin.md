# Plugin

## 它是什么

**plugin** 改的并非模块本身，而是**模块与模块之间的接缝**。模块是积木，plugin 是在缝里动手脚的那层。

它分两类，各管一摊：

- **Prompt plugin**：在 controller 组装 system prompt 时往里面加内容。
- **Lifecycle plugin**：挂在运行时事件上，比如 LLM 调用前后、tool 调用前后、sub-agent 启动前后。

想在**不 fork 模块**的前提下加行为，plugin 基本就是主路。

## 为什么要有它

很多真正有用的 agent 行为，本质上是夹在 tool 与 LLM 之间的规则，而非全新的组件。比如：

- “每次调 bash 前，先过一遍安全策略。”
- “每次调完 LLM，都记一下 token 方便计费。”
- “每次调 LLM 前，先把相关历史事件捞出来塞进 messages。”
- “无论如何都在 system prompt 前面加一段项目专用说明。”

这些事当然也可以靠继承某个模块来做。但那样很容易越改越重：你 fork 一份，上游一改，你就得跟着 rebase。plugin 让你直接钩在接缝上，不碰积木本体。

## 怎么定义它

### Prompt plugin

一个 `BasePlugin` 子类，通常会有：

- `name` 和 `priority`（数字越小，越早出现在 prompt 里）
- `get_content(context) → str | None`，返回一段 prompt 文本；如果返回 `None`，就表示这次不贡献内容

聚合器（`prompt/aggregator.py`）会按 priority 给 plugin 排序，再把输出拼成最终的 system prompt。

内置的有：`ToolListPlugin`（自动工具索引）、`FrameworkHintsPlugin`（怎么调 tool、怎么用 `##commands##`）、`EnvInfoPlugin`（工作目录、日期、平台）、`ProjectInstructionsPlugin`（加载 `CLAUDE.md` / `.claude/rules.md`）。

### Lifecycle plugin

也是 `BasePlugin` 子类，只不过会实现下面这些 hook 里的任意一些：

- `on_load(context)`、`on_unload()`
- `pre_llm_call(messages, **kwargs) → list[dict] | None`
- `post_llm_call(response) → ChatResponse | None`
- `pre_tool_execute(name, args) → dict | None`
- `post_tool_execute(name, result) → ToolResult | None`
- `pre_subagent_run(name, context) → dict | None`
- `post_subagent_run(name, output) → str | None`
- fire-and-forget：`on_tool_start`、`on_tool_end`、`on_llm_start`、`on_llm_end`、`on_processing_start`、`on_processing_end`、`on_startup`、`on_shutdown`、`on_compact_start`、`on_compact_complete`、`on_event`

`pre_*` hook 可以抛 `PluginBlockError("message")` 来中止这次操作。这个 message 会变成 tool 结果，或者变成一个被拦下的 `tool_complete` 事件。

## 怎么实现它

`PluginManager.notify(hook, **kwargs)` 会遍历所有已注册、已启用的 plugin，并等待每个匹配的方法执行。`bootstrap/plugins.py` 会在 agent 启动时加载配置里声明的 plugin；package 声明的 plugin 则可以通过 `kohaku.yaml` 被发现。

## 你能拿它做什么

- **安全护栏。** 用 `pre_tool_execute` plugin 拒绝危险命令。
- **token 记账。** 在 `post_llm_call` 里统计 token，再写到外部存储。
- **无感记忆。** 在 `pre_llm_call` 里对历史事件做 embedding 检索，把相关上下文直接塞到前面；效果上就是对 session history 做 RAG，但不需要显式 tool 调用。
- **聪明护栏。** 写一个 `pre_tool_execute` plugin，里面再跑一个小型 nested agent，判断这次动作该不该放行。plugin 是 Python，agent 也是 Python，所以这事完全合法。见 [patterns](/zh/concepts/patterns.md)。
- **拼 prompt。** 写一个 prompt plugin，根据 scratchpad 状态或 session 元数据动态生成指令。

## 别把它看得太死

plugin 不是必需品。没有 plugin 的 creature 也能跑得很好。但只要你开始冒出这种念头——“我想在整个循环的很多地方都加同一种行为”——那答案十有八九是 plugin，不是新模块。

## 另见

- [Controller](/zh/concepts/modules/controller.md) —— 这些 hook 是在哪触发的。
- [Prompt aggregation](/zh/concepts/impl-notes/prompt-aggregation.md) —— prompt plugin 怎么插进去。
- [Patterns — smart guard, seamless memory](/zh/concepts/patterns.md) —— plugin 里套 agent 的做法。
- [reference/plugin-hooks.md](/zh/reference/plugin-hooks.md) —— 每个 hook 的签名。