# 第一个 Python 嵌入

**问题：** 你想在自己的 Python 应用里直接运行一个 creature，接住它的输出，用代码驱动输入，再和别的代码拼起来。

**完成后：** 你会有一个最小脚本：启动 creature，注入一条输入，用自定义 handler 接收输出，然后干净地关闭。接着再看一遍用 `AgentSession` 做事件流式处理的写法。最后是用同样方式嵌入一个 terrarium。

**前置条件：** 先看 [First Creature（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/tutorials/first-creature.md)。你需要把包安装到能 `import kohakuterrarium` 的环境里。

这个框架里的 agent 不是一份配置，而是一个 Python 对象。配置只是描述它；`Agent.from_path(...)` 会把它构造出来；对象归你自己持有。sub-agent、terrarium 和 session 也是同一种形态。完整的理解方式见 [agent-as-python-object（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/python-native/agent-as-python-object.md)。

## 第 1 步：以 editable 模式安装

目标：让 `kohakuterrarium` 能在你的 venv 里直接导入。

在仓库根目录运行：

```bash
uv pip install -e .[dev]
```

`[dev]` 额外依赖会把你后面可能用到的测试辅助工具一起装上。

## 第 2 步：最小嵌入

目标：构造一个 agent，启动它，给它一条输入，再停掉它。

`demo.py`：

```python
import asyncio

from kohakuterrarium.core.agent import Agent


async def main() -> None:
    agent = Agent.from_path("@kt-defaults/creatures/general")

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

默认的 stdout 输出模块会直接把回复打印出来。这里有三点要注意：

1. `Agent.from_path` 解析 `@kt-defaults/...` 的方式和 CLI 一样。
2. `start()` 会初始化 controller、tools、triggers 和 plugins。
3. `inject_input(...)` 对应的是用户在 CLI 输入模块里手动发一条消息。

## 第 3 步：自己接管输出

目标：把输出接到你自己的代码里，不走 stdout。

```python
import asyncio

from kohakuterrarium.core.agent import Agent


async def main() -> None:
    parts: list[str] = []

    agent = Agent.from_path("@kt-defaults/creatures/general")
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

`replace_default=True` 会关掉 stdout，这样你的 handler 就成了唯一的输出目标。这种写法很适合 Web 后端、机器人，或者任何想自己控制渲染的场景。

## 第 4 步：用 `AgentSession` 做流式处理

目标：拿到一个异步迭代器，而不是 push handler。你想用 `async for` 一段段处理回复时，这种方式更顺手。

```python
import asyncio

from kohakuterrarium.core.agent import Agent
from kohakuterrarium.serving.agent_session import AgentSession


async def main() -> None:
    agent = Agent.from_path("@kt-defaults/creatures/general")
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

`AgentSession` 是 HTTP 和 WebSocket 层使用的那层便于传输的包装。底下还是同一个 agent；它只是把每次 `chat(...)` 调用变成一个 `AsyncIterator[str]`。

## 第 5 步：嵌入整个 terrarium

目标：在 Python 里驱动一套多 agent 配置，而不是通过 CLI。

```python
import asyncio

from kohakuterrarium.terrarium.config import load_terrarium_config
from kohakuterrarium.terrarium.runtime import TerrariumRuntime


async def main() -> None:
    config = load_terrarium_config("@kt-defaults/terrariums/swe_team")
    runtime = TerrariumRuntime(config)

    await runtime.start()
    try:
        # runtime.run() drives the main loop until a stop signal.
        # For a script, you can interact through runtime's API or
        # just let the creatures run to quiescence.
        await runtime.run()
    finally:
        await runtime.stop()


asyncio.run(main())
```

如果你想以编程方式控制正在运行的 terrarium，比如向某个 channel 发消息、启动 creature、观察消息，可以用 `TerrariumAPI`（`kohakuterrarium.terrarium.api`）。terrarium 管理工具走的也是这一层封装。

## 第 6 步：把 agents 当作值来组合

“agent 是 Python 对象”真正有用的地方在这儿：你可以把一个 agent 放进别的东西里。放进 plugin，放进 trigger，放进 tool，也可以放进另一个 agent 的输出模块里。[composition algebra（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/python-native/composition-algebra.md) 提供了几种常见组合方式的操作符：`>>`、`|`、`&`、`*`，分别对应 sequence、fallback、parallel 和 retry。等你发现一串普通函数已经很像一条流水线时，就可以用它们。

## 你学会了什么

- `Agent` 就是普通的 Python 对象：构造、启动、注入输入、停止。
- `set_output_handler` 可以替换输出目标；`AgentSession.chat()` 会把它变成异步迭代器。
- `TerrariumRuntime` 用同样的形状运行整套多 agent 配置。
- CLI 只是这些对象的一个使用方；你的应用也可以是。

## 接下来读什么

- [Agent as a Python object（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/python-native/agent-as-python-object.md) —— 这个概念本身，以及它能带来的写法。
- [Programmatic usage guide（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/guides/programmatic-usage.md) —— 面向任务的 Python 接口说明。
- [Composition algebra（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/python-native/composition-algebra.md) —— 用操作符把 agents 接进 Python 流水线。
- [Python API reference（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/reference/python.md) —— 精确签名。
