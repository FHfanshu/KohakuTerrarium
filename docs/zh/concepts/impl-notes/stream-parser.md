# 流解析器

## 这个问题在解决什么

当 LLM 在流式输出中途发出一次工具调用，框架该在什么时候启动这个工具？

有两个选择：

1. **等这一轮结束。** 先收集所有工具调用，统一分发，拿到结果后，必要时再发起下一次 LLM 调用。
2. **块一闭合就立刻分发。** 每个工具在对应文本块闭合后马上运行，同时 LLM 继续往后输出；等 LLM 说完时，有些工具可能已经跑完了。

第二种响应快得多，尤其是一轮输出很长、里面还有多个工具调用的时候。框架采用的就是这种做法。

## 考虑过的方案

- **轮末分发。** 更简单，但白白浪费了流式输出这段时间；工具实际还是排在 LLM 后面串行执行。
- **推测式分发。** 在 LLM 还在输出时就提前启动工具，如果后面发现块其实没写完整，再取消。这个方案太容易出错。
- **在块闭合时做确定性的状态机分发。** 这就是实际实现。只有在对应文本块完整解析结束时才启动工具，绝不在半截输入上运行。

## 实际做法

LLM 的输出流会按 chunk 逐段送进一个解析器状态机。解析器会根据当前配置的 `tool_format`，跟踪三类可嵌套的块：

- **工具调用** —— 例如 bracket（默认）格式 `[/bash]@@command=ls\n[bash/]`；XML 格式 `<bash command="ls"></bash>`；native 格式则使用 LLM 提供方自己的 function-calling 封装。
- **子 agent 分发** —— 使用同一套格式家族，只是标签换成 agent tag。
- **框架命令** —— `info`、`jobs`、`wait`（以及解析器 `DEFAULT_COMMANDS` 集合里的 `read_job`）。它们和工具调用共用同样的 bracket/XML 包裹方式。格式如何配置，见 [modules/tool](/docs/concepts/modules/tool.md)（英文）和 [modules/plugin](/docs/concepts/modules/plugin.md)（英文）。

当一个块闭合时，解析器会在自己的输出生成器上发出事件。controller 的处理方式如下：

- `TextEvent` → 输出到流。
- `ToolCallEvent` → `Executor.submit_from_event(event, is_direct=True)` → `asyncio.create_task(tool.execute(...))`。这一串会立刻返回。
- `SubAgentCallEvent` → 类似处理，通过 `SubAgentManager.spawn`。
- `CommandEvent` → 内联执行（读取 job 输出、加载文档等）；这类操作很快，而且结果确定。

在流结束时，controller 会等待这段流式输出期间启动的所有 `direct` job，收集它们的结果作为 `tool_complete` 事件，再把这些结果回送给 LLM，进入下一轮。

## 保持不变的约束

- **每个已闭合的块只分发一次。** 不完整的块绝不会运行。
- **同一轮里的多个工具并行运行。** 对它们的 task 做 `gather`，不是按顺序一个个执行。
- **工具执行不会阻塞 LLM 的流式输出。** LLM 继续输出，工具在旁边跑。
- **后台工具不会让这一轮一直悬着。** 被标记为 background 的工具会先返回它的 job id 作为占位；controller 继续往下走；真正结果会在后续事件里送达。

## 代码里的位置

- `src/kohakuterrarium/parsing/` —— 解析器状态机。每种 tool format 变体各有一个模块（bracket、XML、native）。
- `src/kohakuterrarium/core/controller.py` —— 消费解析器事件。
- `src/kohakuterrarium/core/executor.py` —— 把工具执行包装成 task。
- `src/kohakuterrarium/core/agent_tools.py` —— `submit-from-event` 这条路径，把解析器输出接到 executor 上。

## 另见

- [Composing an agent](/docs/concepts/foundations/composing-an-agent.md)（英文）—— 这一页展开的是单轮内部的细节，那一页看的是整轮流程。
- [Tool](/docs/concepts/modules/tool.md)（英文）—— 执行模式（direct / background / stateful）。
