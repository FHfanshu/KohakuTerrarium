# 以代码方式使用

给想把 agent 嵌进自己 Python 代码里的读者。

creature 不是配置文件，配置文件只是用来描述它。真正跑起来的 creature，是一个异步 Python 对象：`Agent`。在 KohakuTerrarium 里，agent、terrarium、session 都能直接调用，也都能 `await`。你的代码负责调度，agent 负责干活。

先补概念可以看：[把 agent 当成 Python 对象](/zh/concepts/python-native/agent-as-python-object.md)、[组合代数](/zh/concepts/python-native/composition-algebra.md)。

## 四个入口

| 接口 | 适用场景 |
|---|---|
| `Agent` | 你想完全自己控制：注入事件、挂自定义输出处理器、自己管生命周期。 |
| `AgentSession` | 流式聊天封装：塞入输入，迭代输出块。适合 bot 和 Web UI。 |
| `TerrariumRuntime` | 你已经有 terrarium 配置，想直接跑起来。 |
| `KohakuManager` | 多租户服务场景：按 ID 管很多 agent 或 terrarium，不绑具体传输层。 |

如果你要在 Python 里做多 agent 流水线，但不想上 terrarium，看[组合](//zh/guides/composition.md)。

## `Agent`：完全控制

```python
import asyncio
from kohakuterrarium.core.agent import Agent

async def main():
    agent = Agent.from_path("@kt-biome/creatures/swe")
    agent.set_output_handler(
        lambda text: print(text, end=""),
        replace_default=True,
    )
    await agent.start()
    await agent.inject_input("Explain what this codebase does.")
    await agent.stop()

asyncio.run(main())
```

常用方法：

- `Agent.from_path(path, *, input_module=..., output_module=..., session=..., environment=..., llm_override=..., pwd=...)`：从配置目录或 `@pkg/...` 引用构建。
- `await agent.start()` / `await agent.stop()`：启动和停止。
- `await agent.run()`：内置主循环，会从输入端拉内容、分发 trigger、运行 controller。
- `await agent.inject_input(content, source="programmatic")`：绕过 input module，直接塞输入。
- `await agent.inject_event(TriggerEvent(...))`：推送任意事件。
- `agent.interrupt()`：停掉当前处理周期，非阻塞。
- `agent.switch_model(profile_name)`：运行时切换 LLM。
- `agent.set_output_handler(fn, replace_default=False)`：新增或替换一个输出 sink。
- `await agent.add_trigger(trigger)` / `await agent.remove_trigger(id)`：运行时增删 trigger。

属性：

- `agent.is_running: bool`
- `agent.tools: list[str]`、`agent.subagents: list[str]`
- `agent.conversation_history: list[dict]`

## `AgentSession`：流式聊天

```python
import asyncio
from kohakuterrarium.serving.agent_session import AgentSession

async def main():
    session = await AgentSession.from_path("@kt-biome/creatures/swe")
    await session.start()
    async for chunk in session.chat("What does this do?"):
        print(chunk, end="")
    print()
    await session.stop()

asyncio.run(main())
```

`chat(message)` 会在 controller 流式输出时不断产出文本块。工具活动和子 agent 事件会通过 output module 的 activity callback 暴露出来。`AgentSession` 主要管文本流；如果你要更完整的事件，就用 `Agent` 加自定义 output module。

构建方法：`AgentSession.from_path(...)`、`from_config(AgentConfig)`、`from_agent(pre_built_agent)`。

## 输出处理

`set_output_handler` 可以挂任意可调用对象：

```python
def handle(text: str) -> None:
    my_logger.info(text)

agent.set_output_handler(handle, replace_default=True)
```

如果你要多个输出目标，比如 TTS、Discord、文件，可以在 YAML 里配 `named_outputs`，agent 会自动分发。

## 事件级控制

```python
from kohakuterrarium.core.events import TriggerEvent, create_user_input_event

await agent.inject_event(create_user_input_event("Hi", source="slack"))
await agent.inject_event(TriggerEvent(
    type="context_update",
    content="User just navigated to page /settings.",
    context={"source": "frontend"},
))
```

`type` 可以是 controller 已经接好要处理的任意字符串，比如 `user_input`、`idle`、`timer`、`channel_message`、`context_update`、`monitor`，也可以是你自定义的类型。见[Python API 参考](/zh/reference/python.md)。

## 在代码里运行 terrarium

```python
import asyncio
from kohakuterrarium.terrarium.runtime import TerrariumRuntime
from kohakuterrarium.terrarium.config import load_terrarium_config
from kohakuterrarium.core.channel import ChannelMessage

async def main():
    config = load_terrarium_config("@kt-biome/terrariums/swe_team")
    runtime = TerrariumRuntime(config)
    await runtime.start()

    tasks = runtime.environment.shared_channels.get("tasks")
    await tasks.send(ChannelMessage(sender="user", content="Fix the auth bug."))

    await runtime.run()
    await runtime.stop()

asyncio.run(main())
```

运行时方法有：`start`、`stop`、`run`、`add_creature`、`remove_creature`、`add_channel`、`wire_channel`。`environment` 里放着所有 creature 都能看到的 `shared_channels`，它是一个 `ChannelRegistry`；每个 creature 也有自己的私有 `Session`。

## `KohakuManager`：多租户

HTTP API、Web 应用，还有那些想“按 ID 管一堆 agent”的代码，都会用到它：

```python
from kohakuterrarium.serving.manager import KohakuManager

manager = KohakuManager(session_dir="/var/kt/sessions")

agent_id = await manager.agent_create("@kt-biome/creatures/swe")
async for chunk in manager.agent_chat(agent_id, "Hi"):
    print(chunk, end="")

status = manager.agent_status(agent_id)
manager.agent_interrupt(agent_id)
await manager.agent_stop(agent_id)
```

它也提供 terrarium、creature、channel 相关操作。manager 会处理 session store 的挂载，也会保证并发访问安全。

## 干净地停止

`start()` 和 `stop()` 要成对出现：

```python
agent = Agent.from_path("...")
try:
    await agent.start()
    await agent.inject_input("...")
finally:
    await agent.stop()
```

也可以用 `AgentSession` 或 `compose.agent()`，它们都是异步上下文管理器。

在任何 asyncio task 里都可以安全调用中断：

```python
agent.interrupt()           # non-blocking
```

controller 会在 LLM 流式生成的各步之间检查中断标志。

## 自定义 session / environment

```python
from kohakuterrarium.core.session import Session
from kohakuterrarium.core.environment import Environment

env = Environment(env_id="my-app")
session = env.get_session("my-agent")
session.extra["db"] = my_db_connection

agent = Agent.from_path("...", session=session, environment=env)
```

你放进 `session.extra` 的东西，tool 都可以通过 `ToolContext.session` 访问。

## 挂接 session 持久化

```python
from kohakuterrarium.session.store import SessionStore

store = SessionStore("/tmp/my-session.kohakutr")
store.init_meta(
    session_id="s1",
    config_type="agent",
    config_path="path/to/creature",
    pwd="/tmp",
    agents=["my-agent"],
)
agent.attach_session_store(store)
```

简单场景下，`AgentSession` 和 `KohakuManager` 会根据 `session_dir` 自动处理。

## 测试

```python
from kohakuterrarium.testing.agent import TestAgentBuilder

env = (
    TestAgentBuilder()
    .with_llm_script([
        "Let me check. [/bash]@@command=ls\n[bash/]",
        "Done.",
    ])
    .with_builtin_tools(["bash"])
    .with_system_prompt("You are helpful.")
    .build()
)

await env.inject("List files.")
assert "Done" in env.output.all_text
assert env.llm.call_count == 2
```

`ScriptedLLM` 的输出是可预测的；`OutputRecorder` 会记录 chunk、write 和 activity，方便断言。

## 排错

- **`await agent.run()` 一直不返回。** `run()` 跑的是完整事件循环。只有 input module 关闭，比如 CLI 收到 EOF，或者触发了终止条件，它才会退出。一次性交互别用它，直接 `inject_input` 然后 `stop` 就行。
- **输出处理器没被调用。** 如果你不想同时往 stdout 打，确认设了 `replace_default=True`；另外先启动 agent，再注入输入。
- **热插入的 creature 一直收不到消息。** 调完 `runtime.add_creature` 后，对每个它要消费的 channel，都要再调一次 `runtime.wire_channel(..., direction="listen")`。
- **`AgentSession.chat` 卡住。** 有别的调用方正在用这个 agent；session 会把输入串行化。一个调用方配一个 `AgentSession`。

## 另见

- [组合](//zh/guides/composition.md) —— Python 侧的多 agent 流水线。
- [自定义模块](//zh/guides/custom-modules.md) —— 自己写并接入 tool、input、output。
- [Python API 参考](/zh/reference/python.md) —— 完整签名。
- [examples/code/](https://github.com/Kohaku-Lab/KohakuTerrarium/tree/main/examples/code) —— 每种模式都有可运行脚本。
