# 插件钩子

这里列出插件可用的全部 hook：生命周期、LLM、工具、sub-agent 和回调。hook 定义在 `kohakuterrarium.modules.plugin` 的 `Plugin` 协议里；`BasePlugin` 提供默认的 no-op 实现。接线位置在 `bootstrap/plugins.py`。

想先看整体模型，读 [concepts/modules/plugin（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/modules/plugin.md)。
想看按任务展开的用法，读 [guides/plugins（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/guides/plugins.md) 和 [guides/custom-modules（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/guides/custom-modules.md)。

## 返回值语义

- **转换类 hook**（`pre_*`、`post_*`）：返回 `None` 表示值不变；返回新值则替换传给下一个插件或框架的输入。
- **回调类 hook**（`on_*`）：返回值会被忽略，调用后不等待后续处理。

## 阻断

任何 `pre_*` hook 都可以抛出 `PluginBlockError` 来直接中止这次操作。框架会把错误抛出来，请求不会继续，对应的 `post_*` hook **不会** 触发。回调类 hook 不能阻断。

---

## 生命周期 hooks

| Hook | Signature | Fired when | Return |
|---|---|---|---|
| `on_load` | `async on_load(ctx: PluginContext) -> None` | Plugin is loaded into an agent. | ignored |
| `on_unload` | `async on_unload() -> None` | Plugin is unloaded or agent stops. | ignored |

`PluginContext` 会把 agent、本身的配置、scratchpad 和 logger 暴露给插件。具体结构见 `kohakuterrarium.modules.plugin.context`。

---

## LLM hooks

| Hook | Signature | Fired when | Return semantics |
|---|---|---|---|
| `pre_llm_call` | `async pre_llm_call(messages: list[dict], **kwargs) -> list[dict] \| None` | Before every LLM request (controller, sub-agent, compact). | `None` keeps the list; a new list replaces it. May raise `PluginBlockError`. |
| `post_llm_call` | `async post_llm_call(response: ChatResponse) -> ChatResponse \| None` | After an LLM response is assembled. | `None` keeps the response; a new `ChatResponse` replaces it. |

---

## 工具 hooks

| Hook | Signature | Fired when | Return semantics |
|---|---|---|---|
| `pre_tool_execute` | `async pre_tool_execute(name: str, args: dict) -> dict \| None` | Before a tool is dispatched to the executor. | `None` keeps `args`; a new dict replaces them. May raise `PluginBlockError`. |
| `post_tool_execute` | `async post_tool_execute(name: str, result: ToolResult) -> ToolResult \| None` | After a tool completes (including error results). | `None` keeps the result; a new `ToolResult` replaces it. |

---

## Sub-agent hooks

| Hook | Signature | Fired when | Return semantics |
|---|---|---|---|
| `pre_subagent_run` | `async pre_subagent_run(name: str, ctx: SubAgentContext) -> dict \| None` | Before a sub-agent is spawned and started. | `None` keeps the spawn context; a dict merges overrides. May raise `PluginBlockError`. |
| `post_subagent_run` | `async post_subagent_run(name: str, output: str) -> str \| None` | After a sub-agent completes (its output is about to be delivered as a `subagent_output` event). | `None` keeps the output; a new string replaces it. |

---

## 回调 hooks

所有回调都是 fire-and-forget。返回值会被忽略。它们通过插件调度器并发运行，所以单个慢回调不会卡住 agent。

| Hook | Signature | Fired when |
|---|---|---|
| `on_tool_start` | `async on_tool_start(name: str, args: dict) -> None` | Tool execution is about to begin. |
| `on_tool_end` | `async on_tool_end(name: str, result: ToolResult) -> None` | Tool execution completed. |
| `on_llm_start` | `async on_llm_start(messages: list[dict]) -> None` | LLM request sent. |
| `on_llm_end` | `async on_llm_end(response: ChatResponse) -> None` | LLM response received. |
| `on_processing_start` | `async on_processing_start() -> None` | Agent enters a processing turn. |
| `on_processing_end` | `async on_processing_end() -> None` | Agent exits a processing turn. |
| `on_startup` | `async on_startup() -> None` | Agent `start()` completed. |
| `on_shutdown` | `async on_shutdown() -> None` | Agent `stop()` is running. |
| `on_compact_start` | `async on_compact_start(reason: str) -> None` | Compaction begins. |
| `on_compact_complete` | `async on_compact_complete(summary: str) -> None` | Compaction finishes. |
| `on_event` | `async on_event(event: TriggerEvent) -> None` | Any event is injected into the controller. |

---

## Prompt 插件（单独一类）

Prompt 插件在 `prompt/aggregator.py` 组装 system prompt 时运行。它们和生命周期插件分开加载。

`BasePlugin`（位于 `kohakuterrarium.prompt.plugins`）提供：

```python
priority: int       # lower = earlier
name: str
async def get_content(self, context: PromptContext) -> str | None
```

- `get_content(context) -> str | None`：返回要插入的文本块；返回 `None` 则表示不提供内容。
- `priority`：排序键。内置插件的值是 50/45/40/30。

内置 prompt 插件见 [builtins.md — Prompt plugins（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/reference/builtins.md#prompt-plugins)。

自定义 prompt 插件通过 creature 配置里的 `plugins` 字段注册，和生命周期插件一样；框架会根据插件类是继承生命周期 `Plugin` 协议，还是 prompt `BasePlugin`，分发到不同路径。

---

## 写一个插件

最小的生命周期插件：

```python
from kohakuterrarium.modules.plugin import BasePlugin, PluginBlockError

class GuardPlugin(BasePlugin):
    async def pre_tool_execute(self, name, args):
        if name == "bash" and "rm -rf" in args.get("command", ""):
            raise PluginBlockError("unsafe command")
        return None  # keep args unchanged
```

在 creature 配置里注册：

```yaml
plugins:
  - name: guard
    type: custom
    module: ./plugins/guard.py
    class: GuardPlugin
```

运行时可以通过 `/plugin toggle guard` 开关（见 [builtins.md — User commands（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/reference/builtins.md#user-commands)），也可以走 HTTP 的 plugin toggle endpoint。

---

## 另见

- Concepts:
  [plugin（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/modules/plugin.md)，
  [patterns（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/patterns.md)。
- Guides:
  [plugins（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/guides/plugins.md)，
  [custom modules（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/guides/custom-modules.md)。
- Reference:
  [python（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/reference/python.md)，
  [configuration（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/reference/configuration.md)，
  [builtins（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/reference/builtins.md)。
