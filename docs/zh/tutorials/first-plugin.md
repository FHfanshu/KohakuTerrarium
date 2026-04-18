# 第一个 Plugin

**问题：**有些行为不属于某一个模块。比如每次 LLM 调用前都塞一点上下文，或者不管在哪里，只要出现某种工具调用模式就直接拦下。这种事，不适合做成新 tool，也不适合做成新输出模块。该用 plugin。

**做完后：**你会在 `config.yaml` 里把两个能跑的 plugin 接到一个 creature 上：

1. 一个**上下文注入器**，给每次 LLM 调用加一条简短的 system message，写上当前 UTC 时间。
2. 一个**工具守卫**，只要 `bash` 调用里带 `rm -rf`，就拦下来，并返回一条模型看得懂的报错信息。

**前提：**先看过[第一个 Creature](first-creature.md)，最好也看过[第一个自定义 Tool](first-custom-tool.md)。你至少得会两件事：改 creature 的 `config.yaml`，还有把 Python 文件放到它旁边。

plugin 改的是**模块之间怎么连**，不是模块本身。为什么边界这样划，可以看[plugin 概念](../concepts/modules/plugin.md)。

## 第 1 步：挑个目录

继续用你现成的 creature，或者新建一个：

```text
creatures/tutorial-creature/
  config.yaml
  plugins/
    utc_injector.py
    bash_guard.py
```

```bash
mkdir -p creatures/tutorial-creature/plugins
```

下面这两个 plugin 都是生命周期 plugin，继承自 `kohakuterrarium.modules.plugin.base` 里的 `BasePlugin`。creature 配置里的 `plugins:` 段，接的就是这种类。

> 注意：框架里还有一种 *prompt plugin*，基类是 `kohakuterrarium.prompt.plugins.BasePlugin`。它们是在构建阶段往 system prompt 里补内容，层级更低，也不是靠配置直接接进去的。像“每次调用前都加点东西”这种需求，用 `pre_llm_call` 生命周期 plugin 更合适。下面就是这种写法。

## 第 2 步：写上下文注入 plugin

`creatures/tutorial-creature/plugins/utc_injector.py`：

```python
"""Inject current UTC time into every LLM call."""

from datetime import datetime, timezone

from kohakuterrarium.modules.plugin.base import BasePlugin, PluginContext


class UTCInjectorPlugin(BasePlugin):
    name = "utc_injector"
    priority = 90  # Late — run after other pre_llm_call plugins.

    async def on_load(self, context: PluginContext) -> None:
        # Nothing to do here; defined to show the lifecycle hook.
        return

    async def pre_llm_call(
        self, messages: list[dict], **kwargs
    ) -> list[dict] | None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        injection = {
            "role": "system",
            "content": f"[utc_injector] Current UTC time: {now}",
        }

        # Insert after the first system message so the agent's real
        # personality prompt stays first.
        modified = list(messages)
        insert_at = 1
        for i, msg in enumerate(modified):
            if msg.get("role") == "system":
                insert_at = i + 1
                break
        modified.insert(insert_at, injection)
        return modified
```

说明：

- `pre_llm_call` 拿到的是即将发出去的完整 `messages` 列表。你可以返回改过的列表来替换它，也可以返回 `None`，表示不改。
- `priority` 是整数。在 `pre_*` hook 里，值越小越早执行；在 `post_*` hook 里，值越小越晚执行。这里用 `90`，是为了排在框架自带 hook 的后面。
- `[utc_injector]` 这个前缀只是个约定。记日志时，你能一眼看出这段内容是哪一个 plugin 加进去的。

## 第 3 步：写工具守卫 plugin

`creatures/tutorial-creature/plugins/bash_guard.py`：

```python
"""Block `bash` calls that contain dangerous patterns."""

from kohakuterrarium.modules.plugin.base import (
    BasePlugin,
    PluginBlockError,
    PluginContext,
)

DANGEROUS_PATTERNS = ("rm -rf",)


class BashGuardPlugin(BasePlugin):
    name = "bash_guard"
    priority = 1  # First — block before anything else runs.

    async def on_load(self, context: PluginContext) -> None:
        return

    async def pre_tool_execute(self, args: dict, **kwargs) -> dict | None:
        tool_name = kwargs.get("tool_name", "")
        if tool_name != "bash":
            return None  # Not our concern.

        command = args.get("command", "") or ""
        for pattern in DANGEROUS_PATTERNS:
            if pattern in command:
                raise PluginBlockError(
                    f"bash_guard: blocked — command contains "
                    f"'{pattern}'. Use a safer approach (explicit paths, "
                    f"trash instead of delete)."
                )
        return None  # Allow.
```

说明：

- `pre_tool_execute` 会收到 `args`，还有像 `tool_name`、`job_id` 这样的关键字参数。先按 `tool_name` 过滤，再看参数内容，因为这个 hook 会对**每一个** tool 调用触发。
- 如果要中止调用，就抛出 `PluginBlockError(message)`。这条 message 会变成 LLM 看到的 tool 结果，所以要写清楚，让模型知道该换个办法。
- 返回 `None` 表示原样放行。返回改过的 dict，则表示在执行前重写参数，比如强制加一个更安全的 flag。

## 第 4 步：把两个 plugin 接到 creature 配置里

`creatures/tutorial-creature/config.yaml`：

```yaml
name: tutorial_creature
version: "1.0"
base_config: "@kt-defaults/creatures/general"

system_prompt_file: prompts/system.md

plugins:
  - name: utc_injector
    type: custom
    module: ./plugins/utc_injector.py
    class: UTCInjectorPlugin

  - name: bash_guard
    type: custom
    module: ./plugins/bash_guard.py
    class: BashGuardPlugin
```

这些字段和上一个教程里接自定义 tool 的方式一样：

- `type: custom` —— 从本地文件加载。
- `module` —— 相对于 agent 目录的路径。
- `class` —— 要实例化的 plugin 类名。`class` 和 `class_name` 都能用。

如果要传配置，用 `options:`。它会作为 dict 传给 `__init__(self, options=...)`。上面的例子不需要选项，所以这里省略了。

## 第 5 步：运行，确认一下

```bash
kt run creatures/tutorial-creature --mode cli
```

### 确认注入器生效

问 agent 一个必须依赖当前时间的问题：

```text
> what time is it right now, in UTC, to the nearest minute?
```

这个 creature 应该会回答一个接近**现在**的时间，哪怕它自己没有原生时钟能力。（如果你的日志级别是 `DEBUG`，还能直接看到插进去的 system message。）

### 确认守卫生效

让 agent 递归删除点东西：

```text
> run: rm -rf /tmp/tutorial-test-dir
```

控制器会分发这次 tool 调用，守卫 plugin 会抛出 `PluginBlockError`，模型拿到的 tool 结果就是那段错误文本。常见反应是“我不能这么做”，然后换个建议。文件不会被删。

## 第 6 步：再看看其他 hook

上面用到的两个 hook 最常见，但不是全部。完整的生命周期 plugin 接口包括：

- 生命周期：`on_load`、`on_unload`、`on_agent_start`、`on_agent_stop`
- LLM：`pre_llm_call`、`post_llm_call`
- Tools：`pre_tool_execute`、`post_tool_execute`
- 子 agent：`pre_subagent_run`、`post_subagent_run`
- 回调：`on_event`、`on_interrupt`、`on_task_promoted`、`on_compact_start`、`on_compact_end`

`pre_*` hook 可以改输入，也可以抛出 `PluginBlockError` 直接中止。`post_*` hook 可以改结果。回调则只是观察，不拦截。完整签名和更多例子可以看[plugins 指南](../guides/plugins.md)，仓库里的 `examples/plugins/` 也有每种 hook 的完整示例。

## 你学到了什么

- plugin 加的是模块**之间**的行为，也就是接缝，不是积木本体。最常用的两个 hook 是 `pre_llm_call`（注入上下文）和 `pre_tool_execute`（拦截或改写）。
- `PluginBlockError` 就是 plugin 说“不行”的方式，而且模型能读懂，接着调整动作。
- `config.yaml` 里的 `plugins:`，接法和 `tools:` 接自定义 tool 基本一样：`type: custom`、`module:`、`class:`。
- `priority` 是整数；在 `pre_*` 里越小越早，在 `post_*` 里越小越晚。

## 接着看

- [Plugin 概念](../concepts/modules/plugin.md) —— 为什么要有 plugin，它能解决什么问题，包括把 agent 放进 plugin 里的模式。
- [Plugins 指南](../guides/plugins.md) —— 完整的 hook 参考和示例。
- [组合模式](../concepts/patterns.md) —— 怎么把这些思路扩展成 “smart guard” 和 “seamless memory” 这类模式。
