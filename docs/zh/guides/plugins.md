# Plugins

给不想 fork 模块本体，只想在模块之间那层接口上加行为的人看。

Plugin 改的是 controller、tools、sub-agents 和 LLM 之间的连接方式，不是模块本身。它分两类：**prompt plugin** 往 system prompt 里塞内容；**lifecycle plugin** 挂在运行时事件上，比如 LLM 前后、tool 前后这些点。

先补概念： [plugin](./concepts/modules/plugin.md)、[patterns](./concepts/patterns.md)。

## 什么时候该写 plugin，什么时候写 tool，什么时候写 module

- *tool*：LLM 可以按名字直接调用的东西。
- *module*（input / output / trigger / sub-agent）：一整块运行时能力。
- *plugin*：夹在它们中间跑的规则，比如拦截、记账、注入 prompt、查 memory。

如果你的需求说出来是“每次 X 前后都要做一下 Y”，那十有八九该写 plugin。

## Prompt plugins

约定是这样的：

- 继承 `BasePlugin`
- 设置 `name`、`priority`（越小越早出现在最终 prompt 里）
- 实现 `get_content(context) -> str | None`

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

内置 prompt plugins（一直都在）：

| Plugin | Priority | Purpose |
|---|---|---|
| `ProjectInstructionsPlugin` | 30 | 加载 `CLAUDE.md` / `.claude/rules.md` |
| `EnvInfoPlugin` | 40 | 工作目录、平台、日期 |
| `FrameworkHintsPlugin` | 45 | tool 调用语法 + 框架命令例子（`info`、`jobs`、`wait`） |
| `ToolListPlugin` | 50 | 每个 tool 的一句话说明 |

priority 越小越早跑。你自己的 plugin 放哪一层，就自己把 priority 选到对应位置。

## Lifecycle plugins

继承 `BasePlugin`，然后按需要实现下面这些 hook。它们全都是 async。

| Hook | Signature | Effect |
|---|---|---|
| `on_load(context)` | setup at agent start | — |
| `on_unload()` | teardown at stop | — |
| `pre_llm_call(messages, **kwargs)` | return `list[dict] \| None` | 替换发给 LLM 的 messages |
| `post_llm_call(response)` | return `ChatResponse \| None` | 替换 response |
| `pre_tool_execute(name, args)` | return `dict \| None`; or raise `PluginBlockError` | 替换参数，或者直接拦掉调用 |
| `post_tool_execute(name, result)` | return `ToolResult \| None` | 替换 tool result |
| `pre_subagent_run(name, context)` | return `dict \| None` | 替换 sub-agent context |
| `post_subagent_run(name, output)` | return `str \| None` | 替换 sub-agent output |

还有一类是 fire-and-forget 回调：没有返回值，也改不了内容：

- `on_tool_start`、`on_tool_end`
- `on_llm_start`、`on_llm_end`
- `on_processing_start`、`on_processing_end`
- `on_startup`、`on_shutdown`
- `on_compact_start`、`on_compact_complete`
- `on_event`

## 例子：tool guard

拦危险 shell 命令。

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

抛出 `PluginBlockError` 之后，这次操作就中止了，这个报错信息会变成 tool result。

## 例子：token 记账

```python
class TokenAccountant(BasePlugin):
    name = "token_accountant"

    async def post_llm_call(self, response):
        usage = response.usage or {}
        my_db.record(tokens_in=usage.get("prompt_tokens"),
                     tokens_out=usage.get("completion_tokens"))
        return None   # 不替换 response
```

## 例子：无感 memory（plugin 里套一个 agent）

可以写一个 `pre_llm_call` plugin，先把相关的历史事件捞出来，再塞到 messages 前面。要判断哪些历史相关，也可以在 plugin 里调一个小的嵌套 agent。Plugin 本质上就是普通 Python，所以里面用 agent 没问题。见 [concepts/python-native/agent-as-python-object](./concepts/python-native/agent-as-python-object.md)。

## 运行时管理 plugin

Slash 命令：

```
/plugin list
/plugin enable tool_guard
/plugin disable tool_guard
/plugin toggle tool_guard
```

Plugin 只会在 agent 启动时加载一次。enable / disable 只是运行时开关，不会重载。你改了配置，还是得重启。

## 分发 plugins

可以打进 package：

```yaml
# my-pack/kohaku.yaml
name: my-pack
plugins:
  - name: tool_guard
    module: my_pack.plugins.tool_guard
    class: ToolGuard
```

使用方在自己的 creature 里启用它：

```yaml
plugins:
  - name: tool_guard
    type: package
    options: { deny_patterns: [...] }
```

见 [Packages](packages.md)。

## Hook 执行顺序

多个 plugin 都实现同一个 hook 时：

- `pre_*` hooks 按注册顺序执行；第一个返回非 `None` 的结果就算数。
- `post_*` hooks 也按注册顺序执行，后一个拿到的是前一个处理后的输出。
- fire-and-forget hooks 会全部执行；出错只记日志，不会往外抛。

如果任意一个 `pre_*` hook 抛出 `PluginBlockError`，后面的 plugin 就都不跑了，这个操作直接短路。

## 测试 plugins

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

- **找不到 plugin class。** 检查 `class`，不是 `class_name`。虽然配置加载器两种都收，但 package manifest 里用的是 `class`。
- **Hook 根本没触发。** 先确认 hook 名字写对了。`pre_llm_call` 和 `pre_tool_execute` 这种拼错，通常就是静悄悄没效果。
- **`PluginBlockError` 抛了，调用还是照样执行。** 你是在 `post_*` hook 里抛的。要拦调用，用 `pre_tool_execute`。
- **多个 plugin 叠起来顺序不对。** `pre_*` hooks 按注册顺序跑，去配置里的 `plugins:` 列表调顺序。

## 另见

- [examples/plugins/](https://github.com/Kohaku-Lab/KohakuTerrarium/tree/main/examples/plugins) —— 每类 hook 都有一个示例。
- [Custom Modules](custom-modules.md) —— plugin 挂着的那些模块怎么自己写。
- [Reference / plugin hooks](./reference/plugin-hooks.md) —— 全部 hook 签名。
- [Concepts / plugin](./concepts/modules/plugin.md) —— 设计思路。