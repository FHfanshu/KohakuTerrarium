# 流解析器

## 这个问题是什么

当 LLM 在流式输出的中途吐出一个工具调用时，框架到底该在什么时候开始跑这个工具？

有两种做法：

1. **等这一轮彻底结束。** 先把所有工具调用都收集起来，再一起分发、拿结果，必要时再发起下一次 LLM 调用。
2. **块一闭合就立刻分发。** 工具和 LLM 剩下的输出并行进行；等 LLM 说完时，有些工具其实已经跑完了。

第二种响应快很多，尤其是一轮里有多个工具调用、而且流式输出又比较长的时候。框架用的就是这个方案。

## 考虑过的方案

- **轮次结束后再分发。** 简单，但把流式输出这段时间白白浪费了；工具等于排在 LLM 后面。
- **推测式分发。** LLM 还在输出时就先启动工具，如果后面发现块没写完整，再取消。太容易出错。
- **块闭合时，由确定性的状态机分发。** 这就是现在的做法。只有文本块完整解析结束后才启动工具，绝不会在半截输入上动手。

## 实际怎么做

LLM 的输出流会被一块一块送进解析器状态机。解析器会根据当前配置的 `tool_format`，跟踪三类可嵌套的块：

- **工具调用** —— 比如 bracket（默认）格式是 `[/bash]@@command=ls\n[bash/]`，XML 格式是 `<bash command="ls"></bash>`，native 格式则用 LLM provider 自己的 function-calling 封装。
- **Sub-agent 分发** —— 用的是同一套格式体系，只是 tag 换成 agent tag。
- **框架命令** —— `info`、`jobs`、`wait`，以及解析器 `DEFAULT_COMMANDS` 集合里的 `read_job`。它们和工具调用共享同样的 bracket/XML 包裹方式。格式怎么配置，可以看 [Tool —— 格式](../modules/tool.md) 和 [Plugin](../modules/plugin.md)。

当某个块闭合后，解析器会通过输出生成器发出一个事件。controller 的处理方式是：

- `TextEvent` → 直接流式输出。
- `ToolCallEvent` → `Executor.submit_from_event(event, is_direct=True)` → `asyncio.create_task(tool.execute(...))`。立刻返回。
- `SubAgentCallEvent` → 类似处理，不过走的是 `SubAgentManager.spawn`。
- `CommandEvent` → 内联执行，比如读取 job 输出、加载文档。这些操作快，而且是确定性的。

到了流结束时，controller 会等待这一轮里启动过的 `direct` jobs，把结果收集成 `tool_complete` 事件，再把这些结果喂回给 LLM，进入下一轮。

## 保住了哪些不变量

- **每个闭合块只分发一次。** 半截块永远不会执行。
- **同一轮里的多个工具会并行跑。** 是对多个 task 做 `gather`，不是按顺序一个个等。
- **LLM 的流式输出不会被工具执行卡住。** LLM 继续说，工具在旁边跑。
- **后台工具不会把当前轮次拖住。** 标记为 background 的工具会先返回一个 job id 作为占位，controller 继续往下走；真正结果会以稍后的事件送达。

## 代码在哪

- `src/kohakuterrarium/parsing/` —— 解析器状态机，按 tool-format 变体分模块实现（bracket、XML、native）。
- `src/kohakuterrarium/core/controller.py` —— 消费解析器事件。
- `src/kohakuterrarium/core/executor.py` —— 把工具执行包装成 task。
- `src/kohakuterrarium/core/agent_tools.py` —— `submit_from_event` 这条路径，把解析器输出接到 executor。

## 另见

- [Composing an agent](../foundations/composing-an-agent.md) —— 这一页放大看的，是那张 turn 级流程图里的局部。
- [Tool](../modules/tool.md) —— 执行模式（direct / background / stateful）。
