# 第一个自定义工具

**问题：**内置工具不够用，你得给 agent 加一个 LLM 能直接调用的新函数。

**做完后：**你会有一个放在 creature 目录里的 `BaseTool` 子类，在 `config.yaml` 里接好，运行时自动加载，模型需要时就能调用。

**前提：**先看[第一个 Creature](first-creature.md)。你手里得先有一个自己的 creature 目录。

这里用一个很简单的 `wordcount` 当例子：输入一段字符串，数一数有几个词。重点不在这点逻辑，而在工具该怎么写、怎么接进去。想看工具还能做什么，去读[工具概念](../concepts/modules/tool.md)。

## 第 1 步：选个目录

先准备一个 creature 目录，专门放这个工具。这里用 `creatures/tutorial-creature/` 举例。工具源码和配置放在一起：

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

- 继承 `BaseTool`，实现 `tool_name`、`description` 和 `_execute`。`BaseTool` 公开的 `execute` 已经包好了 `try/except`，抛异常时会返回 `ToolResult(error=...)`。
- `parameters` 是兼容 JSON Schema 的字典。控制器会拿它生成给 LLM 看的工具 schema。
- `_execute` 是异步方法，返回 `ToolResult`。`output` 可以是字符串，也可以是 `ContentPart` 列表，用来放多模态结果。
- 如果工具需要工作目录、会话或者 scratchpad，把类属性 `needs_context = True` 打开，再让 `_execute` 用关键字参数接收 `context`。完整的 `ToolContext` 见[工具概念](../concepts/modules/tool.md)。

## 第 3 步：接到 creature 配置里

`creatures/tutorial-creature/config.yaml`：

```yaml
name: tutorial_creature
version: "1.0"
base_config: "@kt-biome/creatures/general"

system_prompt_file: prompts/system.md

tools:
  - name: wordcount
    type: custom
    module: ./tools/wordcount.py
    class_name: WordCountTool
```

这几个字段的意思：

- `type: custom`：从本地 Python 文件加载，不是 `builtin` 或 `package`。
- `module`：`.py` 文件路径，相对于 agent 目录 `creatures/tutorial-creature/` 来算。
- `class_name`：这个模块里的类名。

因为 `tools:` 是在继承来的列表后面继续追加，所以 `general` 里原有的工具都会保留，`wordcount` 只是额外加上的。

`creatures/tutorial-creature/prompts/system.md`：

```markdown
# Tutorial Creature

You are a helpful assistant for text experiments. When a user asks
about word counts, prefer the `wordcount` tool.
```

## 第 4 步：跑起来试试

```bash
kt run creatures/tutorial-creature --mode cli
```

输入：

```text
> Count the words in "hello world foo bar"
```

控制器应该会调用 `wordcount`，传入 `text="hello world foo bar"`，最后把结果 `4 words` 显示出来。

退出时，`kt` 还是会照常打印恢复会话的提示。要是你想更稳定地看到它被触发，最好开个新会话，或者直接加 `--no-session` 跑一次性的测试。

## 第 5 步：选对执行模式

工具有三种执行模式：

| Mode | 什么时候用 | 内置示例 |
|---|---|---|
| `DIRECT` | 很快、纯计算、能在当前轮里跑完。下一次 LLM 调用前会先等结果。 | `wordcount`, `read`, `grep` |
| `BACKGROUND` | 运行时间比较长，通常是几秒起。先返回一个任务句柄，结果后面再作为事件送回来。LLM 这时还能继续干别的。 | `bash`（长命令）、子 agent |
| `STATEFUL` | 多轮交互。工具先产出一次，agent 响应后，工具还能继续往下产出。 | 有状态向导、REPL |

`BaseTool` 默认是 `BACKGROUND`。如果不合适，就像上面的例子那样重写 `execution_mode`。纯计算、100 毫秒以内的小工具，一般就该用 `DIRECT`。

执行流程的细节可以看[工具概念：How we implement it](../concepts/modules/tool.md#how-we-implement-it)。流式输出在解析到结束块后就会立刻启动工具；多个 `DIRECT` 工具会通过 `asyncio.gather` 并行跑。

## 第 6 步：用 ScriptedLLM 测一下（可选）

做单元测试时，可以拿一个可预测的 LLM 来驱动控制器。`kohakuterrarium.testing` 里已经带了现成的辅助工具：

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

脚本里工具调用的写法，取决于 creature 的 `tool_format`，也就是 `bracket`、`xml` 或 `native`。如果是原生函数调用，就用对应 provider 的调用格式；如果是 `bracket`（SWE creature 的祖先配置默认就是这个），写成 `[/name]{json}[name/]` 就行。

`OutputRecorder`、`EventRecorder` 和 `TestAgentBuilder` 在 `src/kohakuterrarium/testing/` 里。

## 你学到了什么

- 一个工具就是 `BaseTool` 子类，里面要有 `tool_name`、`description`、`parameters` 和 `_execute`。
- 在 `config.yaml` 里，用 `tools:`、`type: custom`、`module:` 和 `class_name:` 把它接进来。
- 执行模式会直接影响行为。快而纯的工具用 `DIRECT`，耗时任务用 `BACKGROUND`。
- 测试时可以用 `ScriptedLLM` 把整条流程稳定跑一遍。

## 接着看

- [工具概念](../concepts/modules/tool.md)：工具不只是函数，也可以是消息总线、状态句柄、agent 包装层之类的东西。
- [自定义模块指南](../custom-modules.md)：把工具、子 agent、触发器和输出模块放在一起看。
- [第一个 Plugin](first-plugin.md)：如果你想改的并非某个模块内部，而是模块之间怎么衔接，那篇更合适。
