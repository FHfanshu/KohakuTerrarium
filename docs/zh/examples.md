# 示例

给想直接看可运行代码和配置的人准备的。

`examples/` 目录按类型整理了可运行的内容：独立 agent 配置、terrarium 配置、plugin 实现，以及把框架嵌进 Python 代码里的脚本。每个文件夹都对应一种常见写法，你可以直接照着抄，或者拿来继承。

先补一个概念：[边界](./concepts/boundaries.md)。这些示例本来就故意覆盖了不少边角情况。

## `examples/agent-apps/` —— 独立 creatures

单 creature 配置。运行方式：

```bash
kt run examples/agent-apps/<name>
```

| Agent | 模式 | 展示内容 |
|---|---|---|
| `swe_agent` | 编码 agent | 一个重度依赖工具的 creature，风格接近 `kt-biome/creatures/swe` |
| `discord_bot` | 群聊机器人 | 自定义 Discord I/O、ephemeral、原生 tool calling |
| `planner_agent` | plan-execute-reflect | scratchpad 状态机 + critic 子 agent |
| `monitor_agent` | 触发器驱动 | `input: none` + 定时触发器，不需要用户参与 |
| `conversational` | 流式 ASR/TTS | Whisper 输入、TTS 输出、可交互的子 agent |
| `rp_agent` | 角色扮演 | 以内存优先的设计、启动触发器、persona prompt |
| `compact_test` | 压缩压力测试 | 小上下文 + 自动 compact，用来验证 compaction 流程 |

相关指南：[Creatures](creatures.md)、[配置](configuration.md)。

## `examples/terrariums/` —— 多智能体配置

```bash
kt terrarium run examples/terrariums/<name>
```

| Terrarium | 拓扑 | Creatures |
|---|---|---|
| `novel_terrarium` | 带反馈的流水线 | brainstorm → planner → writer |
| `code_review_team` | 带关卡的循环 | developer、reviewer、tester |
| `research_assistant` | 带协调者的星型结构 | coordinator + searcher + analyst |

相关指南：[Terrariums](terrariums.md)。

## `examples/plugins/` —— plugin hooks

每种 hook 类别都给了一个例子。自己写 plugin 时，可以直接拿这些当参照。

| Plugin | Hooks | 难度 |
|---|---|---|
| `hello_plugin` | `on_load`, `on_agent_start/stop` | 初级 |
| `tool_timer` | `pre/post_tool_execute`, state | 初级 |
| `tool_guard` | `pre_tool_execute`, `PluginBlockError` | 中级 |
| `prompt_injector` | `pre_llm_call`（修改消息） | 中级 |
| `response_logger` | `post_llm_call`, `on_event`, `on_interrupt` | 中级 |
| `budget_enforcer` | `pre/post_llm_call`，带阻断和 state | 高级 |
| `subagent_tracker` | `pre/post_subagent_run`, `on_task_promoted` | 高级 |
| `webhook_notifier` | fire-and-forget 回调、`inject_event`、`switch_model` | 高级 |

相关指南：[Plugins](plugins.md)。完整的逐字段说明见 `examples/plugins/README.md`。

## `examples/code/` —— Python 嵌入

这些脚本会把框架嵌进你的代码里，由你的代码负责 orchestration。每个脚本用到的 compose algebra 片段都不一样，调用的也可能是 `Agent`、`TerrariumRuntime`、`KohakuManager` 这些 API。

| Script | 模式 | 用到的特性 |
|---|---|---|
| `programmatic_chat.py` | 把 Agent 当库来用 | `AgentSession.chat()` |
| `run_terrarium.py` | 用代码启动 Terrarium | `TerrariumRuntime`、channel 注入 |
| `discord_adventure_bot.py` | 机器人主导交互 | `agent()`、动态创建、游戏状态 |
| `debate_arena.py` | 多 agent 轮流发言 | `agent()`、`>>`、`async for`、持久 agent |
| `task_orchestrator.py` | 动态 agent 拓扑 | `factory()`、`>>`、`asyncio.gather` |
| `ensemble_voting.py` | 用多样性做冗余 | `&`、`>>` 自动包装、`\|`、`*` |
| `review_loop.py` | 写作 → 评审 → 修改 | `.iterate()`、持久 `agent()` |
| `smart_router.py` | 分类再分发 | `>> {dict}` 路由、`factory()`、`\|` 兜底 |
| `pipeline_transforms.py` | 数据提取流水线 | `>>` 自动包装（`json.loads`、lambdas）、agents + functions |

相关指南：[编程式用法](programmatic-usage.md)、[组合](composition.md)。

## 新读者建议怎么读

1. **先跑一个。** `kt run examples/agent-apps/swe_agent`，先感受一下 creature 是怎么工作的。
2. **再照着改。** 复制这个文件夹，改 `config.yaml`，再跑一遍。
3. **加一个 plugin。** 把 `examples/plugins/tool_timer.py` 放进你 creature 的 `plugins:` 列表里。
4. **再看 Python。** 打开 `examples/code/programmatic_chat.py` 跑一下。
5. **开始组合。** 想看 compose algebra 怎么用，可以试 `examples/code/review_loop.py`。
6. **最后上多智能体。** 运行 `examples/terrariums/code_review_team`，看看 channel 里怎么走消息。

## 另见

- [快速开始](getting-started.md) — 环境准备。
- [`kt-biome`](https://github.com/Kohaku-Lab/kt-biome) — 展示用包；很多示例都沿用了它的写法。
- [教程](./tutorials/README.md) — 和这些示例配套的引导式文档。
