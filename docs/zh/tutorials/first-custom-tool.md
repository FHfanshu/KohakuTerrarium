# 第一个自定义工具

**问题：** 你的智能体需要一种内置工具没有提供的能力。你想给它加一个 LLM 可以调用的新函数。

**完成后：** 你会得到一个 `BaseTool` 子类，文件放在 creature 目录里，在 `config.yaml` 中接好，运行时自动加载，并在需要时由 LLM 调用。

**前提：** [第一个 Creature（英文）](/tutorials/first-creature.md)。你需要先有一个自己可用的 creature 目录。

这里的示例工具是一个很简单的 `wordcount`，用来统计字符串里的单词数。重点在结构，不在逻辑本身。想看工具除了简单函数还能怎么用，可以读[工具概念（英文）](/concepts/modules/tool.md)。

## 第 1 步：选一个目录

先建一个 creature 目录，用它来承载这个工具。这里用 `creatures/tutorial-creature/` 作为例子。工具源码和配置文件放在一起：

```text
creatures/tutorial-creature/
  config.yaml
  prompts/
    system.md
  tools/
    wordcount.py
```

创建目录：

```bash
mkdir -p creatures/tutorial-creature/prompts
mkdir -p creatures/tutorial-creature/tools
```

## 第 2 步：写工具

`creatures/tutorial-creature/tools/wordcount.py`：

```python
"""Word count tool — counts words in a given text."""

from typing import Any

from kohakuterrarium.modules.tool.base import (
    BaseTool,
    ExecutionMode,
    ToolResult,
)


class WordCountTool(BaseTool):
    """Count the words in a string."""

    @property
    def tool_name(self) -> str:
        return "wordcount"

    @property
    def description(self) -> str:
        # One line — goes straight into the system prompt.
        return "Count the words in a given piece of text."

    @property
    def execution_mode(self) -> ExecutionMode:
        # Pure, fast, in-memory — direct mode. See Step 5.
        return ExecutionMode.DIRECT

    # The JSON schema the LLM sees for args.
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to count words in.",
            }
        },
        "required": ["text"],
    }

    async def _execute(self, args: dict[str, Any], **kwargs: Any) -> ToolResult:
        text = args.get("text", "")
        count = len(text.split())
        return ToolResult(
            output=f"{count} words",
            metadata={"count": count},
        )
```

要点：

- 继承 `BaseTool`。实现 `tool_name`、`description` 和 `_execute`。`BaseTool` 里的公共 `execute` 包装层已经处理了 `try/except`，出异常时会返回 `ToolResult(error=...)`。
- `parameters` 是兼容 JSON Schema 的字典。控制器会用它来生成 LLM 能看到的工具 schema。
- `_execute` 是异步方法，返回值是 `ToolResult`。`output` 可以是字符串，也可以是 `ContentPart` 列表，用来表示多模态结果。
- 如果工具需要工作目录、会话或 scratchpad，把类属性 `needs_context = True` 打开，并在 `_execute` 里接收关键字参数 `context`。完整的 `ToolContext` 接口见[工具概念（英文）](/concepts/modules/tool.md)。

## 第 3 步：把工具接到 creature 配置里

`creatures/tutorial-creature/config.yaml`：

```yaml
name: tutorial_creature
version: "1.0"
base_config: "@kt-defaults/creatures/general"

system_prompt_file: prompts/system.md

tools:
  - name: wordcount
    type: custom
    module: ./tools/wordcount.py
    class_name: WordCountTool
```

各字段的作用：

- `type: custom`：从本地 Python 文件加载，而不是 `builtin` 或 `package`。
- `module`：`.py` 文件路径，相对于智能体目录 `creatures/tutorial-creature/` 解析。
- `class_name`：这个模块里的类名。

因为 `tools:` 会在继承来的列表基础上继续追加，所以你会保留 `general` 里原有的整套工具，再额外加上 `wordcount`。

`creatures/tutorial-creature/prompts/system.md`：

```markdown
# Tutorial Creature

You are a helpful assistant for text experiments. When a user asks
about word counts, prefer the `wordcount` tool.
```

## 第 4 步：运行并试一下

```bash
kt run creatures/tutorial-creature --mode cli
```

输入：

```text
> Count the words in "hello world foo bar"
```

控制器应该会调用 `wordcount`，传入 `text="hello world foo bar"`，然后把结果显示出来，也就是 `4 words`。退出时，`kt` 会照常打印恢复会话的提示。如果你想更稳定地看到它触发，可以开一个新会话，或者加 `--no-session` 做一次性的运行。

## 第 5 步：选对执行模式

工具有三种执行模式：

| Mode | 适用场景 | 内置示例 |
|---|---|---|
| `DIRECT` | 很快、纯计算、能在当前轮内完成。下一次 LLM 调用前会先等待结果。 | `wordcount`, `read`, `grep` |
| `BACKGROUND` | 运行时间较长，按秒计。会先返回一个任务句柄，结果作为后续事件到达。LLM 可以继续工作。 | `bash`（长命令）、子智能体 |
| `STATEFUL` | 多轮交互。工具先产出一次，智能体响应后，工具还能继续产出。 | 有状态向导、REPL |

`BaseTool` 默认是 `BACKGROUND`。如果默认值不适合，要像示例那样重写 `execution_mode`。纯计算、100 毫秒以内的小工具，通常应该用 `DIRECT`。

执行流水线的实现见[工具概念：实现方式（英文）](/concepts/modules/tool.md#how-we-implement-it)。流式输出在解析到结束块后就会立即启动工具；多个 `DIRECT` 工具会通过 `asyncio.gather` 并行运行。

## 第 6 步：用 ScriptedLLM 做测试（可选）

做单元测试时，可以用可预测的 LLM 来驱动控制器。`kohakuterrarium.testing` 包自带了几个辅助工具：

```python
import asyncio

from kohakuterrarium.core.agent import Agent
from kohakuterrarium.testing.llm import ScriptedLLM, ScriptEntry


async def test_wordcount() -> None:
    agent = Agent.from_path("creatures/tutorial-creature")
    agent.llm = ScriptedLLM([
        ScriptEntry('[/wordcount]{"text": "one two three"}[wordcount/]'),
        ScriptEntry("Done — 3 words."),
    ])

    await agent.start()
    try:
        await agent.inject_input("count words in 'one two three'")
    finally:
        await agent.stop()


asyncio.run(test_wordcount())
```

脚本里的工具调用语法取决于 creature 的 `tool_format`，也就是 `bracket`、`xml` 或 `native`。如果是原生函数调用，用对应 provider 的调用格式；如果是 `bracket`（SWE creature 的祖先配置默认就是这个），就写成 `[/name]{json}[name/]`。

`OutputRecorder`、`EventRecorder` 和 `TestAgentBuilder` 可以看 `src/kohakuterrarium/testing/`。

## 你学会了什么

- 工具本质上是一个 `BaseTool` 子类，包含 `tool_name`、`description`、`parameters` 和 `_execute`。
- 在 `config.yaml` 里，通过 `tools:`、`type: custom`、`module:` 和 `class_name:` 把它接进来。
- 执行模式会影响行为。快速、纯粹的工作选 `DIRECT`，耗时任务选 `BACKGROUND`。
- 测试时可以用 `ScriptedLLM` 把整条流程稳定地跑起来。

## 接下来可以读什么

- [工具概念（英文）](/concepts/modules/tool.md)：工具不只是函数，还可以是消息总线、状态句柄、智能体包装层等。
- [自定义模块指南（英文）](/guides/custom-modules.md)：把工具、子智能体、触发器和输出模块放在一起看。
- [第一个插件（英文）](/tutorials/first-plugin.md)：如果你要改的行为不在单个模块内部，而是在模块之间的衔接处，就看这个。
