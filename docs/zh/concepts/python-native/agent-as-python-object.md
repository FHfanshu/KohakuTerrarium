# Agent as a Python object

## 它是什么

在 KohakuTerrarium 里，agent 不是 config file；config file 只是描述 agent 的方式。真正跑起来的 agent 是一个 `kohakuterrarium.core.agent.Agent` 实例，也就是异步 Python object。你可以创建它、启动它、给它喂 event，再停掉它。sub-agent 也是同一种东西，只是嵌套在里面。terrarium 也是另一个 Python object，不过它持有的是一组 agent。

这些东西都能 call、能 await、也能组合。

## 为什么重要

大多数 agent 系统会露出两层：

1. 一层 configuration（YAML、JSON），用来定义“这个 agent”。
2. 一层 runtime（通常是 server 或 CLI），读取 config 后跑出行为。

如果你还想在这上面再搭点东西，往往就得进第三层——另一个 process、另一个 container，或者另一套 plugin system。明明函数调用就能解决的事，结果要绕好几圈。

KohakuTerrarium 把这几层压到了一起：你可以直接 `import kohakuterrarium`，加载 config，起一个 agent，调用它，再拿它吐出来的 events 做任何处理。agent 本身就是一个值。值当然也可以放进别的值里。

## 关键接口长什么样

```python
from kohakuterrarium.core.agent import Agent

agent = Agent.from_path("@kt-defaults/creatures/swe")
agent.set_output_handler(lambda text: print(text, end=""), replace_default=True)

await agent.start()
await agent.inject_input("Explain what this codebase does.")
await agent.stop()
```

或者用更适合 transport 的 wrapper：

```python
from kohakuterrarium.serving.agent_session import AgentSession

session = AgentSession(Agent.from_path("@kt-defaults/creatures/swe"))
await session.start()
async for event in session.send_input("What does this do?"):
    print(event)
await session.stop()
```

Terrarium 也是差不多的形状：

```python
from kohakuterrarium.terrarium.runtime import TerrariumRuntime
from kohakuterrarium.terrarium.config import load_terrarium_config

runtime = TerrariumRuntime(load_terrarium_config("@kt-defaults/terrariums/swe_team"))
await runtime.start()
await runtime.run()
await runtime.stop()
```

## 所以你能做什么

真正有用的不只是“agents are Python”，而是“因为 agent 是 Python，module 也是 Python，所以你可以把 agent 塞进任何 module 里”。下面是几个具体模式：

### 把 agent 放进 plugin 里（smart guard）

比如做一个 `pre_tool_execute` plugin，它内部先跑一个小的嵌套 agent，判断这次 tool call 该不该放行。外层 creature 的主对话不会被弄乱；guard 在它自己的上下文里推理。

### 把 agent 放进 plugin 里（seamless memory）

比如一个 `pre_llm_call` plugin，先跑一个很小的 retrieval agent，去搜 session 的 event log（或者外部 vector store），挑出相关的旧内容，再把它注入到 LLM messages 里。从外层 creature 看，它的 memory 就是自然地“变好了”。

### 把 agent 放进 trigger 里（adaptive watcher）

不是写死 `timer: 60s`，而是做一个自定义 trigger，在每次 `fire()` 时先跑一个小 agent。这个 agent 先看看当前状态，再决定要不要唤醒外层 creature。这样做出来的是会看情况的 watcher，不是固定规则。

### 把 agent 放进 tool 里（context-isolated specialist）

tool 被调用时，内部起一个全新的 agent 来干活。对 LLM 来说，它调用这个 tool 的方式和别的 tool 没区别；但这个 tool 背后其实是一整套子系统。子系统需要彻底隔离时，这种做法很好用——比如要换 model、换 tools、换 prompt。

### 把 agent 放进 output module 里（routing receptionist）

有一种 output module，职责就是决定每一段文本该发到*哪里*。规则简单时，写个 switch statement 就行；如果路由判断更细，就可以接一个 agent 进来，让它读流式输出再决定怎么分发。

## 这也解释了那些 cross-reference

[patterns](../patterns.md) 那篇文档把这些模式都用很短的例子写出来了。这篇概念文档想讲清楚的是：*这些都不是什么特殊机制*。它们只是“agent 是 first-class Python value”这件事的直接用法。

## 别把自己框住

你不一定非得用 Python 来做 creature——大多数场景只写 config 就够了。但如果你写着写着撞墙了，开始想要“在 agent 正在执行的某一步里，再塞一个会判断的 agent”，那也不用再引入新的 plugin system。底下那层 Python substrate 本来就在。

## 另见

- [Composition algebra](composition-algebra.md) —— 在 Python 侧拼 pipeline 的那套操作符。
- [Patterns](../patterns.md) —— 这套能力能解锁的一些用法。
- [guides/programmatic-usage.md](../../guides/programmatic-usage.md) —— 这页内容的任务导向版。
- [reference/python.md](../../reference/python.md) —— 函数签名和 API 索引。