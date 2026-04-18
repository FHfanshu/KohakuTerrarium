# 插件

适合那些想在模块之间的衔接处加行为、又不想 fork 任何模块的读者。

插件改的是 controller、tools、sub-agents 和 LLM 之间的连接，不是模块本身。插件分两类：**prompt 插件**负责往 system prompt 里加内容，**lifecycle 插件**挂到运行期事件上，比如 LLM 调用前后、工具执行前后。

概念先看：[plugin（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/modules/plugin.md)、[patterns（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/patterns.md)。

## 什么时候该写插件、工具或模块

- *tool* 是 LLM 可以按名字调用的东西。
- *module*（input/output/trigger/sub-agent）是一整块运行时能力。
- *plugin* 是跑在它们之间的规则，比如拦截、计费、注入提示词、检索记忆。

如果你的需求是“每次 X 前后都做 Y”，那基本该写插件。

## Prompt 插件

约定：

- 继承 `BasePlugin`。
- 设置 `name`、`priority`（值越小，在最终 prompt 里越靠前）。
- 实现 `get_content(context) -> str | None`。

```python
# plugins/project_header.py
from kohakuterrarium.modules.plugin.base import BasePlugin


class ProjectHeaderPlugin(BasePlugin):
    name = "project_header"
    priority = 35          # before ProjectInstructionsPlugin (30)

    def __init__(self, text: str = ""):
        super().__init__()
        self.text = text

    def get_content(self, context) -> str | None:
        if not self.text:
            return None
        return f"## Project Header\n\n{self.text}"
```

内置 prompt 插件（始终存在）：

| 插件 | 优先级 | 作用 |
|---|---|---|
| `ProjectInstructionsPlugin` | 30 | 加载 `CLAUDE.md` / `.claude/rules.md` |
| `EnvInfoPlugin` | 40 | 工作目录、平台、日期 |
| `FrameworkHintsPlugin` | 45 | 工具调用语法和框架命令示例（`info`、`jobs`、`wait`） |
| `ToolListPlugin` | 50 | 每个工具一行说明 |

优先级越低，运行越早。按这个规则给你的插件排位置。

## Lifecycle 插件

继承 `BasePlugin`，实现下面任意 hook。它们都是 async。

| Hook | 签名 | 作用 |
|---|---|---|
| `on_load(context)` | agent 启动时初始化 | — |
| `on_unload()` | 停止时清理 | — |
| `pre_llm_call(messages, **kwargs)` | 返回 `list[dict] \| None` | 替换发给 LLM 的消息 |
| `post_llm_call(response)` | 返回 `ChatResponse \| None` | 替换响应 |
| `pre_tool_execute(name, args)` | 返回 `dict \| None`；或抛出 `PluginBlockError` | 替换参数，或阻止调用 |
| `post_tool_execute(name, result)` | 返回 `ToolResult \| None` | 替换工具结果 |
| `pre_subagent_run(name, context)` | 返回 `dict \| None` | 替换 sub-agent 上下文 |
| `post_subagent_run(name, output)` | 返回 `str \| None` | 替换 sub-agent 输出 |

下面这些回调只通知，不返回值，也不能修改内容：

- `on_tool_start`、`on_tool_end`
- `on_llm_start`、`on_llm_end`
- `on_processing_start`、`on_processing_end`
- `on_startup`、`on_shutdown`
- `on_compact_start`、`on_compact_complete`
- `on_event`

## 示例：工具守卫

阻止危险的 shell 命令。

```python
# plugins/tool_guard.py
from kohakuterrarium.modules.plugin.base import BasePlugin, PluginBlockError


class ToolGuard(BasePlugin):
    name = "tool_guard"

    def __init__(self, deny_patterns: list[str]):
        super().__init__()
        self.deny_patterns = deny_patterns

    async def pre_tool_execute(self, name: str, args: dict) -> dict | None:
        if name != "bash":
            return None
        command = args.get("command", "")
        for pat in self.deny_patterns:
            if pat in command:
                raise PluginBlockError(f"Blocked by tool_guard: {pat!r}")
        return None
```

配置：

```yaml
plugins:
  - name: tool_guard
    type: custom
    module: ./plugins/tool_guard.py
    class: ToolGuard
    options:
      deny_patterns: ["rm -rf /", "dd if=/dev/zero"]
```

抛出 `PluginBlockError` 会中止这次操作，错误消息会变成工具结果。

## 示例：token 记账

```python
class TokenAccountant(BasePlugin):
    name = "token_accountant"

    async def post_llm_call(self, response):
        usage = response.usage or {}
        my_db.record(tokens_in=usage.get("prompt_tokens"),
                     tokens_out=usage.get("completion_tokens"))
        return None   # don't replace the response
```

## 示例：无缝记忆（在插件里放一个 agent）

可以写一个 `pre_llm_call` 插件，取回相关的历史事件，再把它们插到消息前面。你也可以调用一个小型嵌套 agent 来判断哪些内容相关——插件就是普通 Python，所以里面用 agent 没问题。见 [agent-as-python-object（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/python-native/agent-as-python-object.md)。

## 运行时管理插件

Slash 命令：

```
/plugin list
/plugin enable tool_guard
/plugin disable tool_guard
/plugin toggle tool_guard
```

插件只会在 agent 启动时加载一次；enable/disable 只是运行时开关，不会重新加载。改配置后要重启。

## 分发插件

把插件打进一个 package：

```yaml
# my-pack/kohaku.yaml
name: my-pack
plugins:
  - name: tool_guard
    module: my_pack.plugins.tool_guard
    class: ToolGuard
```

使用方在自己的 creature 里启用：

```yaml
plugins:
  - name: tool_guard
    type: package
    options: { deny_patterns: [...] }
```

见 [Packages（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/guides/packages.md)。

## Hook 执行顺序

当多个插件实现了同一个 hook：

- `pre_*` hook 按注册顺序运行；第一个返回非 `None` 的结果生效。
- `post_*` hook 也按注册顺序运行；每个插件接收上一个插件的输出。
- 只通知的 hook 都会执行完；报错会被记录日志，不会抛出。

任何 `pre_*` hook 只要抛出 `PluginBlockError`，后面的插件都不会再继续处理这次操作。

## 测试插件

```python
from kohakuterrarium.testing.agent import TestAgentBuilder

env = (
    TestAgentBuilder()
    .with_llm_script(["[/bash]@@command=rm -rf /\n[bash/]", "Stopped."])
    .with_builtin_tools(["bash"])
    .with_plugin(ToolGuard(deny_patterns=["rm -rf /"]))
    .build()
)
await env.inject("cleanup")
assert any("Blocked" in act[1] for act in env.output.activities)
```

## 排错

- **找不到插件类。** 检查 `class`，不是 `class_name`。插件这里用的是 `class`。配置加载器两种都接受，但 package manifest 用的是 `class`。
- **Hook 一直没触发。** 先确认 hook 名字写对了；`pre_llm_call` 和 `pre_tool_execute` 这种拼错时不会报错，只会静默失效。
- **抛了 `PluginBlockError`，调用还是执行了。** 这个错误是从 `post_*` hook 抛出来的。要拦截，得用 `pre_tool_execute`。
- **依赖顺序的插件叠加不对。** `pre_*` hook 按注册顺序跑，去配置里的 `plugins:` 列表调整顺序。

## 另见

- [examples/plugins/（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/tree/main/examples/plugins) —— 每类 hook 都有一个示例。
- [Custom Modules（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/guides/custom-modules.md) —— 插件围绕着它们工作。
- [Reference / plugin hooks（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/reference/plugin-hooks.md) —— 所有 hook 签名。
- [Concepts / plugin（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/modules/plugin.md) —— 设计原因。
