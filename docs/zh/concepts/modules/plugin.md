# 插件

## 它是什么

**插件**改的是*模块之间的连接*，不是模块本身。模块是积木，插件跑在接缝上。

它分两种，各管一类问题：

- **Prompt 插件**：controller 构造 system prompt 时，往里补内容。
- **Lifecycle 插件**：挂到运行期事件上，比如 LLM 调用前后、工具调用前后、sub-agent 启动前后。

要在*不 fork 任何模块*的前提下加行为，插件基本就是主要做法。

## 为什么会有它

很多真正有用的 agent 行为，既不是新工具，也不是新 LLM，而是跑在两者之间的一条规则。比如：

- “每次调用 bash 前，先按安全策略检查一遍。”
- “每次调用 LLM 后，统计 token 用量，用来计费。”
- “每次调用 LLM 前，先取回相关历史事件，再塞进消息里。”
- “总是在 system prompt 前面加一段项目专用说明。”

这些事也能靠继承某个模块来做，但那样改动大，也脆。你 fork 一份，上游一更新，又得自己 rebase。

插件不用碰积木本身，只接到缝上就行。

## 我们怎么定义它

### Prompt 插件

继承 `BasePlugin`，并提供：

- `name` 和 `priority`（值越小，越早出现在 prompt 里）
- `get_content(context) -> str | None`，返回一段 prompt 文本；如果不需要输出，就返回 `None`

聚合器 `prompt/aggregator.py` 会按 `priority` 给已注册插件排序，再把它们的输出拼成最终的 system prompt。

内置插件有：`ToolListPlugin`（自动生成工具索引）、`FrameworkHintsPlugin`（说明怎么调用工具、怎么用 `##commands##`）、`EnvInfoPlugin`（工作目录、日期、平台）、`ProjectInstructionsPlugin`（加载 `CLAUDE.md` / `.claude/rules.md`）。

### Lifecycle 插件

同样继承 `BasePlugin`，然后实现下面任意 hook：

- `on_load(context)`、`on_unload()`
- `pre_llm_call(messages, **kwargs) -> list[dict] | None`
- `post_llm_call(response) -> ChatResponse | None`
- `pre_tool_execute(name, args) -> dict | None`
- `post_tool_execute(name, result) -> ToolResult | None`
- `pre_subagent_run(name, context) -> dict | None`
- `post_subagent_run(name, output) -> str | None`
- 只通知、不改值的 hook：`on_tool_start`、`on_tool_end`、`on_llm_start`、`on_llm_end`、`on_processing_start`、`on_processing_end`、`on_startup`、`on_shutdown`、`on_compact_start`、`on_compact_complete`、`on_event`

`pre_*` hook 可以抛出 `PluginBlockError("message")` 来中止操作。这个消息会变成工具结果，或者变成被拦截的 `tool_complete` 事件。

## 我们怎么实现它

`PluginManager.notify(hook, **kwargs)` 会遍历所有已注册、已启用的插件，找到匹配的方法后逐个 await。`bootstrap/plugins.py` 会在 agent 启动时加载配置里声明的插件；package 里声明的插件则通过 `kohaku.yaml` 发现。

## 所以它能做什么

- **安全守卫。** 写一个 `pre_tool_execute` 插件，拦掉危险命令。
- **Token 记账。** 在 `post_llm_call` 里统计 token，再写到外部存储。
- **无缝记忆。** 在 `pre_llm_call` 里对历史事件做 embedding 检索，把相关上下文加到前面；本质上就是不靠工具调用、直接对 session history 做 RAG。
- **智能守卫。** 写一个 `pre_tool_execute` 插件，里面跑一个小型*嵌套 agent*，判断这次动作能不能放行。插件是 Python，agent 也是 Python，所以这完全可行。见 [patterns（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/patterns.md)。
- **Prompt 组合。** 写一个 prompt 插件，把来自 scratchpad 状态或 session 元数据的动态指令塞进去。

## 别被模块框住

插件是可选的。没有插件，creature 也能正常工作。

但如果你开始觉得“这个行为我想在整个循环里都加上”，答案通常是插件，不是新模块。

## 另见

- [Controller（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/modules/controller.md) —— hook 在哪里触发。
- [Prompt aggregation（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/impl-notes/prompt-aggregation.md) —— prompt 插件怎么插进去。
- [Patterns — smart guard, seamless memory（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/patterns.md) —— 插件里放 agent 的模式。
- [reference/plugin-hooks.md（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/reference/plugin-hooks.md) —— 所有 hook 签名。
