# 第一个 Python 嵌入

你想在自己的 Python 应用里直接跑一个 creature：接住它的输出、用代码给它喂输入，再把它和你现有的逻辑接起来。

这篇做完，你会拿到一个最小脚本：启动一个 creature，塞一条输入，用自定义 handler 接输出，然后正常关掉。后面再看同样的事怎么用 `AgentSession` 做事件流。最后再看怎么用一样的方式把整个 terrarium 嵌进去。

前提是先看过 [第一个 Creature](first-creature.md)。另外，你得把包装到能 `import kohakuterrarium` 的环境里。

这个框架里的 agent 不是一份 config，而是 Python 对象。config 只是描述它；`Agent.from_path(...)` 会把它建出来，而这个对象就在你手里。sub-agent、terrarium、session 也是这一路子。完整思路可以看 [Agent as a Python object](../concepts/python-native/agent-as-python-object.md)。

## 第 1 步：用 editable 方式安装

目标很简单：让你的虚拟环境能直接 `import kohakuterrarium`。

在仓库根目录执行：

```bash
uv pip install -e .[dev]
```

`[dev]` 还会顺手装上一些测试辅助依赖，后面可能用得上。

## 第 2 步：最小嵌入

目标：创建一个 agent，启动它，喂一条输入，再停掉。

`demo.py`：

```python
import asyncio

from kohakuterrarium.core.agent import Agent


async def main() -> None:
    agent = Agent.from_path("@kt-biome/creatures/general")

    await agent.start()
    try:
        await agent.inject_input(
            "In one sentence, what is a creature in KohakuTerrarium?"
        )
    finally:
        await agent.stop()


asyncio.run(main())
```

运行：

```bash
python demo.py
```

默认的 stdout 输出模块会直接把回答打出来。这里有三点要注意：

1. `Agent.from_path` 解析 `@kt-biome/...` 的方式和 CLI 一样。
2. `start()` 会初始化 controller、tools、triggers 和 plugins。
3. `inject_input(...)` 就是代码版的“用户在 CLI 输入模块里敲了一条消息”。

## 第 3 步：自己接管输出

目标：别再往 stdout 打，改成进你自己的代码。

```python
import asyncio

from kohakuterrarium.core.agent import Agent


async def main() -> None:
    parts: list[str] = []

    agent = Agent.from_path("@kt-biome/creatures/general")
    agent.set_output_handler(
        lambda text: parts.append(text),
        replace_default=True,
    )

    await agent.start()
    try:
        await agent.inject_input(
            "Explain the difference between a creature and a terrarium."
        )
    finally:
        await agent.stop()

    print("".join(parts))


asyncio.run(main())
```

`replace_default=True` 会把 stdout 关掉，这样输出只会进你的 handler。做 web 后端、bot，或者任何想自己控制渲染的东西时，一般就是这个写法。

## 第 4 步：用 `AgentSession` 做流式输出

目标：拿到一个异步迭代器，而不是 push handler。要是你想用 `async for` 一段一段读响应，这种更顺手。

```python
import asyncio

from kohakuterrarium.core.agent import Agent
from kohakuterrarium.serving.agent_session import AgentSession


async def main() -> None:
    agent = Agent.from_path("@kt-biome/creatures/general")
    session = AgentSession(agent)

    await session.start()
    try:
        async for chunk in session.chat(
            "Describe three practical uses of a terrarium."
        ):
            print(chunk, end="", flush=True)
        print()
    finally:
        await session.stop()


asyncio.run(main())
```

`AgentSession` 是 HTTP 和 WebSocket 那层在用的包装。底下还是同一个 agent，只是每次 `chat(...)` 会给你一个 `AsyncIterator[str]`。

## 第 5 步：嵌入整个 terrarium

目标：不用 CLI，直接从 Python 驱动一套多 agent 配置。

```python
import asyncio

from kohakuterrarium.terrarium.config import load_terrarium_config
from kohakuterrarium.terrarium.runtime import TerrariumRuntime


async def main() -> None:
    config = load_terrarium_config("@kt-biome/terrariums/swe_team")
    runtime = TerrariumRuntime(config)

    await runtime.start()
    try:
        # runtime.run() 会一直跑主循环，直到收到停止信号。
        # 写脚本时，你可以通过 runtime 的 API 交互，
        # 也可以直接让 creatures 自己跑到停下来。
        await runtime.run()
    finally:
        await runtime.stop()


asyncio.run(main())
```

如果你想在 terrarium 跑着的时候直接控制它，比如往某个 channel 发消息、启动一个 creature、观察消息，可以用 `TerrariumAPI`（`kohakuterrarium.terrarium.api`）。terrarium 管理工具走的也是这一层。

## 第 6 步：把 agent 当成值来组合

“agent 是 Python 对象”真正有用的地方，在于你可以把它塞进别的东西里：plugin、trigger、tool，甚至另一个 agent 的 output module 里都行。[Composition algebra](../concepts/python-native/composition-algebra.md) 给了几种常见组合方式的操作符：`>>`、`|`、`&`、`*`，分别对应串联、兜底、并行、重试。你要是已经开始把普通函数拼成一条 pipeline 了，就可以看看这套东西。

## 你学到了什么

- `Agent` 就是普通的 Python 对象：创建、启动、注入输入、停止。
- `set_output_handler` 可以换掉输出去向；`AgentSession.chat()` 会把它变成异步迭代器。
- `TerrariumRuntime` 跑整套多 agent 配置，形状其实也差不多。
- CLI 只是这些对象的一种用法，你自己的应用也可以直接拿来用。

## 接下来可以看什么

- [Agent as a Python object](../concepts/python-native/agent-as-python-object.md) —— 讲清楚这个概念，以及它能带来哪些写法。
- [Programmatic usage guide](../guides/programmatic-usage.md) —— 按任务来查 Python 接口怎么用。
- [Composition algebra](../concepts/python-native/composition-algebra.md) —— 怎么把 agent 接进 Python pipeline。
- [Python API reference](../reference/python.md) —— 具体函数签名都在这里。
