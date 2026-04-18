# 自定义模块

给想自己写 tool、input、output、trigger 或 sub-agent 的人看。

KohakuTerrarium 里所有可扩展的地方，本质上都是 Python protocol。你把 protocol 实现好，再在配置里指向自己的模块，剩下的交给框架。不用改框架源码。

先补概念：[模块](/zh/concepts/modules/README.md)。各模块的概念页也都在 `/zh/concepts/modules/` 下面。

## 自定义模块长什么样

每个模块就是一个 Python 文件，放哪都行。一般会放在 creature 目录里，或者放进一个 package。配置里填 `module: ./path/to/file.py` 和 `class_name: YourClass`。

这五类模块接线方式都差不多，真正不同的只是你的类要实现哪个 protocol。

## Tools

约定在 `kohakuterrarium.modules.tool.base`：

- `async execute(args: dict, context: ToolContext | None) -> ToolResult`
- 可选类属性：`needs_context`、`parallel_allowed`、`timeout`、`max_output`
- 可选 `get_full_documentation() -> str`（框架命令 `info` 会读取它）

最小示例：

```python
# tools/my_tool.py
from kohakuterrarium.modules.tool.base import BaseTool, ToolContext, ToolResult


class MyTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="Do the thing.",
            parameters={
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                },
                "required": ["target"],
            },
            needs_context=True,
        )

    async def execute(self, args: dict, context: ToolContext | None = None) -> ToolResult:
        target = args["target"]
        # context.pwd, context.session, context.environment, context.file_guard, ...
        return ToolResult(output=f"Did the thing to {target}.")
```

配置：

```yaml
tools:
  - name: my_tool
    type: custom
    module: ./tools/my_tool.py
    class_name: MyTool
```

Tool 的执行模式在 `BaseTool` 里设置：

- **direct**（默认）—— 当前 turn 里直接等待执行完成，结果会变成一个 `tool_complete` 事件。
- **background** —— 提交后立刻返回 job id，结果稍后到。
- **stateful** —— 有点像 generator，会跨多个 turn 产出中间结果。

测试：

```python
from kohakuterrarium.testing.agent import TestAgentBuilder
env = (
    TestAgentBuilder()
    .with_llm_script(["[/my_tool]@@target=x\n[my_tool/]", "Done."])
    .with_tool(MyTool())
    .build()
)
await env.inject("do it")
assert "Did the thing to x" in env.output.all_text
```

## Inputs

约定在 `kohakuterrarium.modules.input.base`：

- `async start()` / `async stop()`
- `async get_input() -> TriggerEvent | None`

如果输入读完了，就返回 `None`。这会触发 agent 关闭。

```python
# inputs/line_file.py
import asyncio
import aiofiles
from kohakuterrarium.core.events import TriggerEvent, create_user_input_event
from kohakuterrarium.modules.input.base import BaseInputModule


class LineFileInput(BaseInputModule):
    def __init__(self, path: str):
        super().__init__()
        self.path = path
        self._lines: asyncio.Queue[str] = asyncio.Queue()
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._read())

    async def _read(self) -> None:
        async with aiofiles.open(self.path) as f:
            async for line in f:
                await self._lines.put(line.strip())
        await self._lines.put(None)  # sentinel

    async def get_input(self) -> TriggerEvent | None:
        line = await self._lines.get()
        if line is None:
            return None
        return create_user_input_event(line, source="line_file")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
```

配置：

```yaml
input:
  type: custom
  module: ./inputs/line_file.py
  class_name: LineFileInput
  options:
    path: ./tasks.txt
```

## Outputs

约定在 `kohakuterrarium.modules.output.base`：

- `async start()`、`async stop()`
- `async write(content: str)` —— 完整消息
- `async write_stream(chunk: str)` —— 流式输出的分片
- `async flush()`
- `async on_processing_start()`、`async on_processing_end()`
- `def on_activity(activity_type: str, detail: str)` —— tool / sub-agent 事件
- 可选 `async on_user_input(text)`、`async on_resume(events)`

```python
# outputs/discord.py
import httpx
from kohakuterrarium.modules.output.base import BaseOutputModule


class DiscordWebhookOutput(BaseOutputModule):
    def __init__(self, webhook_url: str):
        super().__init__()
        self.webhook_url = webhook_url
        self._buf: list[str] = []

    async def start(self) -> None:
        self._client = httpx.AsyncClient()

    async def stop(self) -> None:
        await self._client.aclose()

    async def write(self, content: str) -> None:
        await self._client.post(self.webhook_url, json={"content": content})

    async def write_stream(self, chunk: str) -> None:
        self._buf.append(chunk)

    async def flush(self) -> None:
        if self._buf:
            await self.write("".join(self._buf))
            self._buf.clear()

    async def on_processing_start(self) -> None: ...
    async def on_processing_end(self) -> None:
        await self.flush()

    def on_activity(self, activity_type: str, detail: str) -> None:
        pass
```

配置：

```yaml
output:
  type: custom
  module: ./outputs/discord.py
  class_name: DiscordWebhookOutput
  options:
    webhook_url: "${DISCORD_WEBHOOK}"
```

也可以把它挂成一个具名 side-channel。这样主输出还是 stdout，但 tool 可以把内容发到这里：

```yaml
output:
  type: stdout
  named_outputs:
    discord:
      type: custom
      module: ./outputs/discord.py
      class_name: DiscordWebhookOutput
      options: { webhook_url: "${DISCORD_WEBHOOK}" }
```

## Triggers

约定在 `kohakuterrarium.modules.trigger.base`：

- `async wait_for_trigger() -> TriggerEvent | None`
- 可选 `async _on_start()`、`async _on_stop()`
- 可选类属性：`resumable`、`universal`
- 如果 `resumable` 为真：`to_resume_dict()` / `from_resume_dict()`

最小 timer 示例：

```python
# triggers/timer.py
import asyncio
from kohakuterrarium.modules.trigger.base import BaseTrigger
from kohakuterrarium.core.events import TriggerEvent


class TimerTrigger(BaseTrigger):
    resumable = True

    def __init__(self, interval: float, prompt: str | None = None):
        super().__init__(prompt=prompt)
        self.interval = interval

    async def wait_for_trigger(self) -> TriggerEvent | None:
        await asyncio.sleep(self.interval)
        return self._create_event("timer", f"Timer fired after {self.interval}s")

    def to_resume_dict(self) -> dict:
        return {"interval": self.interval, "prompt": self.prompt}
```

配置：

```yaml
triggers:
  - type: custom
    module: ./triggers/timer.py
    class_name: TimerTrigger
    options: { interval: 60 }
    prompt: "Check the dashboard."
```

如果类上写了 `universal: True`，agent 就能在运行时自己安装这个 trigger。你需要在类里补上 `setup_tool_name`、`setup_description`、`setup_param_schema`，也可以额外提供 `setup_full_doc`。然后在 creature 配置的 `tools:` 下面声明一项，写上 `type: trigger` 和 `name: <setup_tool_name>`。框架会把这个类包成一个同名 tool；一旦调用，就会通过 agent 的 `TriggerManager` 在后台装上对应 trigger。

## Sub-agents

Sub-agent 一般由 `SubAgentConfig` 定义。它本身是个配置 dataclass，所以大多数时候你不用直接去继承 `SubAgent`。常见做法是提供一个 Python 模块，导出一个配置对象：

```python
# subagents/specialist.py
from kohakuterrarium.modules.subagent.config import SubAgentConfig

SPECIALIST_CONFIG = SubAgentConfig(
    name="specialist",
    description="Does niche analysis.",
    system_prompt="You analyze X. Return a short summary.",
    tools=["read", "grep"],
    interactive=False,
    can_modify=False,
    llm="claude-haiku",
)
```

配置：

```yaml
subagents:
  - name: specialist
    type: custom
    module: ./subagents/specialist.py
    config_name: SPECIALIST_CONFIG
```

如果你的 sub-agent 要包住一整个自定义 agent，比如接另一个框架，或者完全用 Python-first 的方式来实现，那就去继承 `SubAgent`，自己实现 `async run(input_text) -> SubAgentResult`。细节见[模块 / Sub-agent](/zh/concepts/modules/sub-agent.md)。

## 给自定义模块打包

可以直接把这些模块放进一个 package：

```
my-pack/
  kohaku.yaml
  my_pack/
    __init__.py
    tools/my_tool.py
    plugins/my_plugin.py
  creatures/
    my-agent/
      config.yaml
```

`kohaku.yaml`：

```yaml
name: my-pack
version: "0.1.0"
creatures: [{ name: my-agent }]
tools:
  - name: my_tool
    module: my_pack.tools.my_tool
    class: MyTool
python_dependencies:
  - httpx>=0.27
```

这样别的配置就可以写 `type: package`，框架会从 `my_pack.tools.my_tool:MyTool` 里取这个类。

相关内容见 [Packages](/zh/packages-and-install-advanced.md)。

## 测试自定义模块

`kohakuterrarium.testing` 里的 `TestAgentBuilder` 会给你一个完整 agent，里面带 `ScriptedLLM` 和 `OutputRecorder`。你可以直接把自己的模块塞进去测：

```python
from kohakuterrarium.testing.agent import TestAgentBuilder

env = (
    TestAgentBuilder()
    .with_llm_script([...])
    .with_tool(MyTool())
    .build()
)
await env.inject("...")
assert env.output.all_text == "..."
```

测 trigger 的话，用 `EventRecorder`，然后检查 `TriggerEvent` 的结构。

## 排错

- **找不到模块。** `module:` 路径是相对 creature 目录解析的。如果这里容易搞混，就直接写绝对路径。
- **Tool 没进 prompt。** 跑一下 `kt info path/to/creature`。很多时候不是没加载，而是被静默拒掉了；先确认 `class_name` 写对。
- **测试里写了 `needs_context=True`，但 `context` 是 `None`。** `TestAgentBuilder` 本来会给 context。要是你还需要 channels 或 scratchpad，记得再补 `.with_session(...)`。
- **Trigger 不能恢复。** 在类上设 `resumable = True`，再实现 `to_resume_dict()`。

## 另见

- [Plugins](plugins.md) —— 想改的是模块之间那层连接，而不是模块本身，就看这个。
- [Packages](/zh/packages-and-install-advanced.md) —— 怎么把模块打包出去复用。
- [Reference / Python API](/zh/reference/python.md) —— `BaseTool`、`BaseInputModule`、`BaseOutputModule`、`BaseTrigger`、`SubAgentConfig`。
- [Concepts / 模块](/zh/concepts/modules/README.md) —— 每个模块一页。
