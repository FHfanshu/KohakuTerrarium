# Sub-agent

## 它是什么

**sub-agent** 是父级 creature 为了某个边界明确的任务，临时拉起来的一个嵌套 creature。它有自己的 LLM 对话、自己的 tool（通常只是父级 tool 的一个子集），还有自己那份较小的上下文。任务结束后，它会回一个压缩过的结果，然后消失。

如果用一句很短的话概括：**它其实也算一种 tool**。从父 controller 的角度看，调用 sub-agent 和调用别的 tool 没本质区别。

## 为什么要有它

上下文窗口是有限的。一个像“去把这个 repo 翻一遍，然后告诉我 auth 怎么工作的”这种任务，可能要读上百个文件。要是把这整个探索过程都塞进父级对话里，主任务的预算马上就被吃光。放到 sub-agent 里做，就等于另外开了个预算，最后只把摘要带回来。

还有一个原因是**专业化**。一个专门拿来做 review 决策的 `critic` sub-agent，通常会比一个通用 agent 顺手兼做 review 更靠谱。sub-agent 让你把专家塞进通才流程里，而不用把整个通才重写一遍。

## 怎么定义它

sub-agent = 一份 creature 配置 + 父级 registry。拉起来之后：

- 它会继承父级的 LLM 和 tool 格式；
- 它只拿到一部分 tool，也就是 sub-agent 配置里 `tools` 列出来的那些；
- 它会跑完整的 Agent 生命周期：start → event-loop → stop；
- 它的结果会作为 `subagent_output` 事件送回父级；如果设了 `output_to: external`，也可以直接把文本流给用户。

有三种形态比较重要：

- **One-shot**（默认）—— 拉起，跑完，回一次结果就结束。
- **Output sub-agent**（`output_to: external`）—— 它的文本会直接并行流到父级 `OutputRouter`，有时甚至替代父 controller 的文本。常见场景是：controller 在后台安静调度，真正让用户看的，是这个 sub-agent 的输出。
- **Interactive**（`interactive: true`）—— 跨多个 turn 持续存在，会接收上下文更新，也可以继续喂新 prompt。适合那种靠会话连续性吃饭的专家角色，比如长期在线的 reviewer 或 planner。

## 怎么实现它

`SubAgentManager`（`modules/subagent/manager.py`）会把 `SubAgent`（`modules/subagent/base.py`）起成 `asyncio.Task`，按 job id 跟踪，并把完成结果作为 `TriggerEvent` 送回去。

深度会被 `max_subagent_depth`（配置级别）限制住，防止递归失控。取消是协作式的：父级可以调用 `stop_task` 去中断正在运行的 sub-agent。

内置 sub-agent（来自 `kt-biome` 和框架）包括：`worker`、`plan`、`explore`、`critic`、`response`、`research`、`summarize`、`memory_read`、`memory_write`、`coordinator`。

## 你能拿它做什么

- **计划 / 实现 / 评审。** 父级挂三个 sub-agent。父级负责编排，每个 sub-agent 只盯自己那一段。
- **安静的 controller。** 父级把 `response` sub-agent 设成 `output_to: external`。controller 自己不往外说话，真正到用户眼前的是 sub-agent 的回复。这也是很多 kt-biome 聊天型 creature 的做法。
- **持续在线的专家。** 一个 `interactive: true` 的 reviewer，可以看见每个 turn，但只在真有话说的时候插嘴。
- **嵌套 terrarium。** sub-agent 自己还能用 `terrarium_create` 拉起一个 terrarium。底层并不在意。
- **纵向套横向。** terrarium 里的某个 creature 自己又用 sub-agent。两种 multi-agent 轴线可以混着来。

## 别把它看得太死

sub-agent 不是必需的。很多短任务，只有 tool 也完全够用。而且“sub-agent”本来就在概念上很像“一个实现恰好是完整 agent 的 tool”。边界有时会变得很模糊：某个 Python tool 里自己起一个 agent，从 LLM 的视角看，这和直接调 sub-agent 几乎没区别。

## 另见

- [Tool](/zh/concepts/modules/tool.md) —— “其实也是 tool”这个视角。
- [Multi-agent overview](/zh/concepts/multi-agent/README.md) —— 纵向（sub-agent）和横向（terrarium）的区别。
- [Patterns — silent controller](/zh/concepts/patterns.md) —— output sub-agent 这种常见写法。
- [reference/builtins.md — Sub-agents](/zh/reference/builtins.md) —— 内置工具包。