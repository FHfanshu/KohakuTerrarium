# 自定义模块

给要自己写 tool、input、output、trigger 或 sub-agent 的人看。

KohakuTerrarium 里所有可扩展的部分，都是 Python protocol。你实现对应 protocol，把配置指到你的模块上，剩下的交给框架。不用改框架源码。

概念预习：[modules](/concepts/modules/README.md)（英文），以及 `/concepts/modules/` 下各模块的页面（英文）。

## 自定义模块的基本形式

每个模块都放在一个 Python 文件里，位置随你定。常见做法是放在 creature 目录下，或者放进一个 package。配置里写 `module: ./path/to/file.py` 和 `class_name: YourClass`。

五种模块的接线方式都一样。区别只在于类实现的是哪个 protocol。

## Tools

约定见 `kohakuterrarium.modules.tool.base`：

- `async execute(args: dict, context: ToolContext | None) -> ToolResult`
- 可选类属性：`needs_context`、`parallel_allowed`、`timeout`、`max_output`
- 可选 `get_full_documentation() -> str`（由框架命令 `info` 加载）

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

Tool 执行模式（通过 `BaseTool` 设置）：

- **direct**（默认）— 在当前 turn 里 await，结果会变成一个 `tool_complete` 事件。
- **background** — 提交后立刻返回 job id；结果稍后到达。
- **stateful** — 类似 generator，会跨多个 turn 产出中间结果。

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

约定见 `kohakuterrarium.modules.input.base`：

- `async start()` / `async stop()`
- `async get_input() -> TriggerEvent | None`

输入耗尽时返回 `None`，这会触发 agent 关闭。

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

约定见 `kohakuterrarium.modules.output.base`：

- `async start()`、`async stop()`
- `async write(content: str)` — 完整消息
- `async write_stream(chunk: str)` — 流式分块
- `async flush()`
- `async on_processing_start()`、`async on_processing_end()`
- `def on_activity(activity_type: str, detail: str)` — tool/subagent 事件
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

也可以把它作为命名 side-channel 使用。主输出仍然走 stdout，tool 可以把内容路由到这里：

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

约定见 `kohakuterrarium.modules.trigger.base`：

- `async wait_for_trigger() -> TriggerEvent | None`
- 可选 `async _on_start()`、`async _on_stop()`
- 可选类属性：`resumable`、`universal`
- 如果启用 `resumable`：`to_resume_dict()` / `from_resume_dict()`

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

`universal: True` 表示这个类可以由 agent 自己安装。你需要在类上补齐 `setup_tool_name`、`setup_description`、`setup_param_schema`，以及可选的 `setup_full_doc`，然后在 creature 配置的 `tools:` 下声明一个 `type: trigger`、`name: <setup_tool_name>` 的条目。框架会把这个类包成一个同名 tool；调用后会通过 agent 的 `TriggerManager` 在后台安装 trigger。

## Sub-agents

Sub-agent 由 `SubAgentConfig` 定义。它本身是配置 dataclass，通常不需要直接继承 `SubAgent`。更常见的做法是提供一个导出配置对象的 Python 模块：

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

如果你的 sub-agent 其实包了一整个自定义 agent，比如基于另一个框架，或者是 Python-first 的实现，那就继承 `SubAgent`，实现 `async run(input_text) -> SubAgentResult`。见 [concepts/modules/sub-agent](/concepts/modules/sub-agent.md)（英文）。

## 打包自定义模块

可以直接放进一个 package：

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

这样一来，别的配置就可以用 `type: package` 来引用，框架会从 `my_pack.tools.my_tool:MyTool` 里取出这个类。

见 [Packages](/guides/packages.md)（英文）。

## 测试自定义模块

`kohakuterrarium.testing` 里的 `TestAgentBuilder` 会给你一个完整 agent，里面带 `ScriptedLLM` 和 `OutputRecorder`。你可以直接把模块塞进去测试：

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

测试 trigger 时，用 `EventRecorder`，检查 `TriggerEvent` 的结构是否正确。

## 排错

- **找不到模块。** `module:` 路径是相对 creature 目录解析的。如果这里说不清，就直接用绝对路径。
- **Tool 没出现在 prompt 里。** 跑 `kt info path/to/creature` 看看。多数时候是这个 tool 被静默拒绝了，先确认 `class_name` 写对了。
- **测试里明明设了 `needs_context=True`，但 `context` 还是 `None`。** `TestAgentBuilder` 会提供 context；如果你还需要 channel 或 scratchpad，确认已经调用了 `.with_session(...)`。
- **Trigger 不能 resume。** 在类上设 `resumable = True`，并实现 `to_resume_dict()`。

## 另见

- [Plugins](/guides/plugins.md)（英文）— 处理模块之间衔接处的行为，比如前后置 hook。
- [Packages](/guides/packages.md)（英文）— 把模块打包出去复用。
- [Reference / Python API](/reference/python.md)（英文）— `BaseTool`、`BaseInputModule`、`BaseOutputModule`、`BaseTrigger`、`SubAgentConfig`。
- [Concepts / modules](/concepts/modules/README.md)（英文）— 每种模块各有一页说明。
