# 示例

如果你想找能直接运行的代码和配置，可以从这里开始。

`examples/` 目录按类型归类了可运行的内容：独立 agent 配置、terrarium 配置、插件实现，以及把框架嵌入 Python 程序的脚本。每个文件夹都对应一种可直接照着用或继承的写法。

概念预读：[boundaries](/concepts/boundaries.md)（英文）—— 这些示例本来就有意覆盖边界情况。

## `examples/agent-apps/` —— 独立 creatures

单个 creature 的配置。运行方式：

```bash
kt run examples/agent-apps/<name>
```

| Agent | 模式 | 展示内容 |
|---|---|---|
| `swe_agent` | 编码 agent | 重工具的 creature，和 `kt-defaults/creatures/swe` 很接近 |
| `discord_bot` | 群聊机器人 | 自定义 Discord I/O、ephemeral、原生 tool 调用 |
| `planner_agent` | plan-execute-reflect | Scratchpad 状态机 + critic 子 agent |
| `monitor_agent` | 触发驱动 | `input: none` + 定时器触发，不需要用户参与 |
| `conversational` | 流式 ASR/TTS | Whisper 输入、TTS 输出、交互式子 agent |
| `rp_agent` | 角色扮演 | 以 memory 为先的设计、启动触发器、persona prompt |
| `compact_test` | 压缩压力测试 | 小上下文 + auto-compact，用来验证 compaction 路径 |

相关指南：[Creatures](/guides/creatures.md)（英文）、[Configuration](/guides/configuration.md)（英文）。

## `examples/terrariums/` —— 多智能体配置

```bash
kt terrarium run examples/terrariums/<name>
```

| Terrarium | 拓扑 | Creatures |
|---|---|---|
| `novel_terrarium` | 带反馈的流水线 | brainstorm → planner → writer |
| `code_review_team` | 带关卡的循环 | developer、reviewer、tester |
| `research_assistant` | 带协调者的星型结构 | coordinator + searcher + analyst |

相关指南：[Terrariums](/guides/terrariums.md)（英文）。

## `examples/plugins/` —— 插件 hooks

每种 hook 类别各有一个例子。自己写插件时，可以先对照这里。

| Plugin | Hooks | 难度 |
|---|---|---|
| `hello_plugin` | `on_load`, `on_agent_start/stop` | beginner |
| `tool_timer` | `pre/post_tool_execute`, state | beginner |
| `tool_guard` | `pre_tool_execute`, `PluginBlockError` | intermediate |
| `prompt_injector` | `pre_llm_call`（消息修改） | intermediate |
| `response_logger` | `post_llm_call`, `on_event`, `on_interrupt` | intermediate |
| `budget_enforcer` | 带阻断和状态的 `pre/post_llm_call` | advanced |
| `subagent_tracker` | `pre/post_subagent_run`, `on_task_promoted` | advanced |
| `webhook_notifier` | fire-and-forget 回调、`inject_event`、`switch_model` | advanced |

相关指南：[Plugins](/guides/plugins.md)（英文）。完整的逐字段说明见 `examples/plugins/README.md`。

## `examples/code/` —— Python 嵌入

这些脚本把框架嵌入到你的代码里，由你的代码负责 orchestration。每个脚本都用了不同一部分 compose algebra，或 `Agent` / `TerrariumRuntime` / `KohakuManager` API。

| Script | 模式 | 使用的特性 |
|---|---|---|
| `programmatic_chat.py` | 把 Agent 当库用 | `AgentSession.chat()` |
| `run_terrarium.py` | 从代码启动 Terrarium | `TerrariumRuntime`、channel 注入 |
| `discord_adventure_bot.py` | 由 bot 掌控交互 | `agent()`、动态创建、游戏状态 |
| `debate_arena.py` | 多 agent 轮流发言 | `agent()`、`>>`、`async for`、持久 agent |
| `task_orchestrator.py` | 动态 agent 拓扑 | `factory()`、`>>`、`asyncio.gather` |
| `ensemble_voting.py` | 用多样性做冗余 | `&`、`>>` 自动包装、`\|`、`*` |
| `review_loop.py` | 写作 → 审查 → 修订 | `.iterate()`、持久 `agent()` |
| `smart_router.py` | 分类并分发 | `>> {dict}` 路由、`factory()`、`\|` 回退 |
| `pipeline_transforms.py` | 数据提取流水线 | `>>` 自动包装（`json.loads`、lambda）、agents + functions |

相关指南：[Programmatic Usage](/guides/programmatic-usage.md)（英文）、[Composition](/guides/composition.md)（英文）。

## 给新读者的阅读顺序

1. **先跑一个。** `kt run examples/agent-apps/swe_agent`，感受一下 creature 是怎么工作的。
2. **再从它改。** 复制这个文件夹，改 `config.yaml`，重新运行。
3. **加一个插件。** 把 `examples/plugins/tool_timer.py` 放进你的 creature 的 `plugins:` 列表。
4. **转到 Python。** 打开 `examples/code/programmatic_chat.py` 并运行。
5. **试试组合。** 看 `examples/code/review_loop.py`，compose algebra 在里面怎么用。
6. **最后跑多智能体。** 运行 `examples/terrariums/code_review_team`，看看 channel 里的流转。

## 另见

- [Getting Started](/guides/getting-started.md)（英文）—— 环境设置。
- [`kt-defaults`](https://github.com/Kohaku-Lab/kt-defaults)（英文）—— 展示用包，很多示例都沿用了里面的模式。
- [Tutorials](/tutorials/README.md)（英文）—— 和这些示例配套的引导式教程。
