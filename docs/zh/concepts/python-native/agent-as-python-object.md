# Agent 作为 Python 对象

## 它是什么

在 KohakuTerrarium 里，agent 不是配置文件。配置文件只是描述它。一个正在运行的 agent，是一个 `kohakuterrarium.core.agent.Agent` 实例：异步 Python 对象。你可以创建它、启动它、给它喂事件，再停掉它。sub-agent 也是同一种对象，只是嵌套在里面。terrarium 也是另一个 Python 对象，只不过它持有的是好几个 agent。

所有这些东西都能调用、能 `await`、能组合。

## 为什么这很重要

大多数 agent 系统会分成两层：

1. 用配置层（YAML、JSON）描述“这个 agent”。
2. 再由运行时层（通常是服务器或 CLI）读取配置，把它跑起来。

你真想在上面继续搭东西，往往还得再加第三层：另一个进程、另一个容器，或者另一套插件系统。本来一次函数调用就能做完的事，结果要绕好几跳。

KohakuTerrarium 把这些层压到了一起：你可以 `import kohakuterrarium`，加载配置，拉起一个 agent，调用它，拿到它吐出的事件，接着随你怎么处理。agent 是一个值。值可以放进别的值里。

## 关键接口长什么样

```python
from kohakuterrarium.core.agent import Agent

agent = Agent.from_path("@kt-defaults/creatures/swe")
agent.set_output_handler(lambda text: print(text, end=""), replace_default=True)

await agent.start()
await agent.inject_input("Explain what this codebase does.")
await agent.stop()
```

或者用更适合传输层的封装：

```python
from kohakuterrarium.serving.agent_session import AgentSession

session = AgentSession(Agent.from_path("@kt-defaults/creatures/swe"))
await session.start()
async for event in session.send_input("What does this do?"):
    print(event)
await session.stop()
```

Terrarium 也是同样的形状：

```python
from kohakuterrarium.terrarium.runtime import TerrariumRuntime
from kohakuterrarium.terrarium.config import load_terrarium_config

runtime = TerrariumRuntime(load_terrarium_config("@kt-defaults/terrariums/swe_team"))
await runtime.start()
await runtime.run()
await runtime.stop()
```

## 所以你可以做什么

真正有用的地方，不是“agent 是 Python”，而是“既然 agent 是 Python，模块也是 Python，那你就可以把 agent 塞进任何模块里”。下面是几种具体模式：

### 把 agent 放进插件里（智能守卫）

写一个 `pre_tool_execute` 插件，在实现里跑一个小型嵌套 agent，判断这次 tool call 要不要放行。外层 creature 的主对话保持干净；守卫 agent 在自己的上下文里做判断。

### 把 agent 放进插件里（无缝记忆）

一个 `pre_llm_call` 插件运行一个很小的检索 agent，去搜当前 session 的事件日志（或者外部向量库），挑出相关的历史内容，再注入到 LLM 消息里。对外层 creature 来说，就是它的记忆“更好用了”。

### 把 agent 放进 trigger 里（自适应观察者）

不是写 `timer: 60s`，而是自定义一个 trigger，让它的 `fire()` 每次触发时都先跑一个小 agent。这个 agent 看当前状态，再决定要不要唤醒外层 creature。这样得到的是不按固定规则走的环境感知。

### 把 agent 放进 tool 里（上下文隔离的专家）

有一种 tool，被调用时会临时拉起一个全新的 agent 来干活。对 LLM 来说，它和调用别的 tool 没区别；但在 tool 的实现内部，其实是一整套子系统。适合那种必须彻底隔离的子系统：不同模型、不同工具、不同 prompt。

### 把 agent 放进 output 模块里（分流前台）

output 模块的工作，是决定每一段文本该送到哪里。简单规则用 `switch` 就够了；要是分流逻辑更细，就接一个 agent，让它读流式输出，再决定怎么路由。

## 由此打通的交叉用法

[/concepts/patterns.md](/concepts/patterns.md)（英文）这份文档给这些模式都配了最小示例。这一页只是想说明：这些都不是什么特殊机制。它们只是“agent 是一等 Python 值”这个事实的直接用法。

## 别把自己框住

你不一定非得用 Python 来构建 creature。大多数场景里，只写配置就够了。但如果某个 creature 配到一半碰了墙，你开始想要“在 agent 正在执行的某一步里，再塞进一个会判断的 agent”，那 Python 这一层已经在那里了，不用再引入新的插件系统。

## 另见

- [Composition algebra](/concepts/python-native/composition-algebra.md)（英文）— Python 侧 pipeline 的组合操作。
- [Patterns](/concepts/patterns.md)（英文）— 这套东西还能怎么用。
- [guides/programmatic-usage.md](/guides/programmatic-usage.md)（英文）— 这页的任务导向版本。
- [reference/python.md](/reference/python.md)（英文）— 签名和 API 索引。
