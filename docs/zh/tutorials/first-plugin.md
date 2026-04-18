# 第一个 Plugin

**问题：**你需要一种不属于任何单个模块的行为。比如，给每次 LLM 调用都加一点上下文，或者在全局范围拦住某种工具调用模式。这时候，新建 tool 不合适；新建输出模块也不合适。该用 plugin。

**完成后：**你会在 `config.yaml` 里把两个能工作的 plugin 接到一个 creature 上：

1. 一个**上下文注入器**，给每次 LLM 调用都加一条简短的 system message，写入当前 UTC 时间。
2. 一个**工具守卫**，拦下任何包含 `rm -rf` 的 `bash` 调用，并返回一条模型能读懂的报错信息。

**前提：**先看过[第一个 Creature](/tutorials/first-creature.md)（英文），最好也看过[第一个自定义 Tool](/tutorials/first-custom-tool.md)（英文）。你至少得熟悉两件事：改 creature 的 `config.yaml`，以及把 Python 文件放在它旁边。

plugin 改的是**模块之间的连接方式**，不是模块本身。为什么边界要这样划，见[plugin 概念](/concepts/modules/plugin.md)（英文）。

## 第 1 步：选一个目录

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

下面两个 plugin 都是生命周期 plugin，它们继承的是 `kohakuterrarium.modules.plugin.base` 里的 `BasePlugin`。在 creature 配置的 `plugins:` 段里，接的就是这类类。

> 注意：框架里还有一种 *prompt plugin*，基类是 `kohakuterrarium.prompt.plugins.BasePlugin`。它们在构建阶段往 system prompt 里补内容，属于更底层的原语，也不是通过配置直接接进去的。像“给每次调用都加点东西”这种需求，用 `pre_llm_call` 生命周期 plugin 更对路，下面就是这么做的。

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

- `pre_llm_call` 拿到的是将要发送出去的完整 `messages` 列表。你可以返回改过的列表来替换它，或者返回 `None`，表示不动。
- `priority` 是整数。在 `pre_*` hook 里，值越小越早跑；在 `post_*` hook 里，值越小越晚跑。这里用 `90`，是为了排在框架自带 hook 的后面。
- `[utc_injector]` 这个前缀只是个约定。你记日志时，能一眼看出是哪一个 plugin 加了这段内容。

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

- `pre_tool_execute` 会收到 `args`，以及像 `tool_name`、`job_id` 这样的关键字参数。先按 `tool_name` 过滤，再去看参数内容；因为这个 hook 会对**每一个** tool 调用触发。
- 想中止调用，就抛 `PluginBlockError(message)`。这条 message 会变成 LLM 看到的 tool 结果，所以要写得足够清楚，让模型知道该换个做法。
- 返回 `None` 表示原样放行。返回改过的 dict，则表示在执行前重写参数，比如强制加一个更安全的 flag。

## 第 4 步：把两个 plugin 接进 creature 配置

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

这些字段和上一个教程里接自定义 tool 的方式是一样的：

- `type: custom` —— 从本地文件加载。
- `module` —— 相对于 agent 目录的路径。
- `class` —— 要实例化的 plugin 类名。`class` 和 `class_name` 都可以。

如果要传配置，用 `options:`，它会作为 dict 传进 `__init__(self, options=...)`。上面的例子不需要选项，所以这里省略了。

## 第 5 步：运行并确认

```bash
kt run creatures/tutorial-creature --mode cli
```

### 确认注入器生效

问 agent 一个必须依赖当前时间的问题：

```text
> what time is it right now, in UTC, to the nearest minute?
```

这个 creature 应该会回答一个接近**当前时刻**的时间，哪怕它本身没有原生时钟能力。（如果你的日志级别是 `DEBUG`，还能直接看到注入进去的 system message。）

### 确认守卫生效

让 agent 递归删除某个东西：

```text
> run: rm -rf /tmp/tutorial-test-dir
```

控制器会分发这次 tool 调用，守卫 plugin 会抛出 `PluginBlockError`，模型拿到的 tool 结果就是那段错误文本。常见反应是“我不能这么做”，然后给出别的建议。文件不会被动到。

## 第 6 步：了解剩下的 hook 面

上面用到的两个 hook 只是最常见的一对。完整的生命周期 plugin 接口包括：

- 生命周期：`on_load`、`on_unload`、`on_agent_start`、`on_agent_stop`
- LLM：`pre_llm_call`、`post_llm_call`
- Tools：`pre_tool_execute`、`post_tool_execute`
- 子 agent：`pre_subagent_run`、`post_subagent_run`
- 回调：`on_event`、`on_interrupt`、`on_task_promoted`、`on_compact_start`、`on_compact_end`

`pre_*` hook 可以改输入，也可以抛出 `PluginBlockError` 直接中止。`post_*` hook 可以改结果。回调则是只观察、不拦截。完整签名和更多例子见[plugins 指南](/guides/plugins.md)（英文），仓库里的 `examples/plugins/` 也有每一种 hook 的完整示例。

## 你学到了什么

- plugin 加的是模块**之间**的行为，也就是接缝，不是积木本体。最常用的两个 hook 是 `pre_llm_call`（注入上下文）和 `pre_tool_execute`（拦截或改写）。
- `PluginBlockError` 就是 plugin 说“不行”的方式，而且模型能读懂并据此调整动作。
- `config.yaml` 里的 `plugins:` 接法，和 `tools:` 接自定义 tool 基本一样：`type: custom`、`module:`、`class:`。
- `priority` 是整数；在 `pre_*` 里越小越早，在 `post_*` 里越小越晚。

## 接着看

- [Plugin 概念](/concepts/modules/plugin.md)（英文）—— 为什么要有 plugin，它能解决什么问题，包括把 agent 放进 plugin 里的模式。
- [Plugins 指南](/guides/plugins.md)（英文）—— 完整 hook 参考和示例。
- [组合模式](/concepts/patterns.md)（英文）—— 如何把这些思路扩展成 “smart guard” 和 “seamless memory” 这类模式。
