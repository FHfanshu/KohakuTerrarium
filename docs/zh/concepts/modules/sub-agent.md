# Sub-agent（子智能体）

## 它是什么

**Sub-agent** 是父级 creature 为某个边界明确的任务临时拉起的嵌套 creature。它有自己的一段 LLM 对话、自己的一组工具（通常是父级工具的子集），还有自己的一小块上下文。任务做完后，它返回一份压缩过的结果，然后结束。

幻灯片里的总结更直接：*它其实也是一种工具*。对父级 controller 来说，调用 sub-agent 和调用别的工具没有区别。

## 为什么需要它

上下文窗口是有限的。像“把这个仓库摸一遍，然后告诉我认证是怎么工作的”这种真实任务，往往要读几百个文件。如果这些探索都塞进父级对话里，主任务的上下文预算很快就没了。放到 sub-agent 里，花的是另一份预算，回来的只有总结。

另一个原因是**专门化**。比如一个专门为评审决策写提示词的 `critic` sub-agent，通常会比一个顺手做评审的通用 agent 更稳。sub-agent 让你把专家角色接进通用工作流里，不用把整个通用 agent 重写一遍。

## 怎么定义

一个 sub-agent 由一份 creature 配置和父级注册表组成。启动后：

- 它继承父级的 LLM 和工具格式。
- 它只拿到一部分工具，也就是 sub-agent 配置里的 `tools` 列表。
- 它会跑完整的 Agent 生命周期：start → event-loop → stop。
- 它的结果会作为父级上的 `subagent_output` 事件送回；如果设了 `output_to: external`，也可以直接流给用户。

有三种形式需要分清：

- **One-shot**（默认）—— 启动，跑到结束，返回一次结果。
- **Output sub-agent**（`output_to: external`）—— 它的文本会和 controller 的文本并行，或者直接替代 controller，经由父级的 `OutputRouter` 流出去。可以把它理解成：controller 在后台安静调度，用户真正看到的是 sub-agent 的输出。
- **Interactive**（`interactive: true`）—— 它会跨轮次保留，能接收上下文更新，也能继续吃新的提示。适合那些需要连续对话的专门角色，比如持续工作的 reviewer，或者常驻 planner。

## 怎么实现

`SubAgentManager`（`modules/subagent/manager.py`）会把 `SubAgent`（`modules/subagent/base.py`）作为 `asyncio.Task` 启动，按 job id 跟踪它们，并把完成结果作为 `TriggerEvent` 送出。

深度由 `max_subagent_depth`（配置级）限制，避免递归失控。取消是协作式的：父级可以调用 `stop_task` 中断一个还在运行的 sub-agent。

内置 sub-agent（在 `kt-defaults` 和框架里）包括：`worker`、`plan`、`explore`、`critic`、`response`、`research`、`summarize`、`memory_read`、`memory_write`、`coordinator`。

## 所以你能怎么用

- **Plan / implement / review。** 父级下面挂三个 sub-agent。父级负责调度，每个 sub-agent 只盯一个阶段。
- **Silent controller。** 父级对 `response` sub-agent 使用 `output_to: external`。controller 自己不直接发文本，用户只会看到 sub-agent 的回复。`kt-defaults` 里大多数聊天型 creature 都是这么做的。
- **Persistent specialist。** 一个 `interactive: true` 的 reviewer，每一轮都能看到，但只在它真有话要说时开口。
- **Nested terrariums。** sub-agent 可以用 `terrarium_create` 再起一个 terrarium。底层并不在意。
- **Vertical-inside-horizontal。** 一个 terrarium creature 自己再用 sub-agent，也就是把多智能体的两条轴混在一起。

## 别被它限制

sub-agent 不是必需的。只有工具的 creature，已经足够处理大多数短任务。而且从概念上说，所谓“sub-agent”就是“实现方式刚好是一整个 agent 的工具”，所以这条边界本来就会发虚：一个工具完全可以在 Python 里启动 agent；从 LLM 的角度看，这和调用 sub-agent 没区别。

## 另见

- [Tool](/docs/concepts/modules/tool.md)（英文）—— “它其实也是工具”这个视角。
- [Multi-agent overview](/docs/concepts/multi-agent/README.md)（英文）—— 纵向（sub-agent）和横向（terrarium）的区别。
- [Patterns — silent controller](/docs/concepts/patterns.md)（英文）—— output sub-agent 这种写法。
- [reference/builtins.md — Sub-agents](/docs/reference/builtins.md)（英文）—— 内置工具包。
