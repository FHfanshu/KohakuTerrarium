# 测试

测试套件放在 `tests/` 下，分为单元测试（`tests/unit/`）和集成测试（`tests/integration/`）。`src/kohakuterrarium/testing/` 下有一套可复用的测试支架，用来用假的 LLM 构造 agent。

## 运行测试

```bash
pytest                                    # 完整测试套件
pytest tests/unit                         # 只跑单元测试
pytest tests/integration                  # 只跑集成测试
pytest -k channel                         # 名称里包含 "channel" 的测试
pytest tests/unit/test_phase3_4.py::test_executor_parallel
pytest -x                                 # 遇到第一个失败就停止
pytest --no-header -q                     # 更安静的输出
```

测试应在完整的 asyncio 环境里运行。异步测试函数用 `pytest-asyncio`（`@pytest.mark.asyncio`）。不要在测试里调用 `asyncio.run()`，把事件循环交给插件管理。

## 测试支架

`src/kohakuterrarium/testing/` 导出四个基础组件。从包根导入：

```python
from kohakuterrarium.testing import (
    ScriptedLLM, ScriptEntry,
    OutputRecorder,
    EventRecorder, RecordedEvent,
    TestAgentBuilder,
)
```

### ScriptedLLM — 可预测的 LLM mock

`testing/llm.py`。它在不调用真实 API 的情况下实现了 `LLMProvider` 协议。给它一组响应，它会按顺序返回。

```python
# 最简单：直接给字符串
llm = ScriptedLLM(["Hello.", "I'll use a tool.", "Done."])

# 进阶：用 ScriptEntry 按匹配条件选择，并控制流式输出。
# 工具调用语法必须和 parser 的 tool_format 一致，默认是
# bracket: [/name]@@arg=value\nbody[name/]
llm = ScriptedLLM([
    ScriptEntry("I'll search.", match="find"),   # 只有最后一条用户消息包含 "find" 时才会命中
    ScriptEntry("Sorry, can't.", match="help"),
    ScriptEntry("[/bash]@@command=echo hi\n[bash/]", chunk_size=5),
])
```

`ScriptEntry`（`testing/llm.py:12`）字段：

- `response: str` —— 完整文本，可以包含框架格式的工具调用。
- `match: str | None` —— 如果设置了，只有最后一条用户消息包含这个子串时才使用该条目，否则跳过。
- `delay_per_chunk: float` —— 每次产出 chunk 之间的秒数。
- `chunk_size: int` —— 每次产出的字符数，默认 10。

一次运行后，可以检查：

- `llm.call_count`
- `llm.call_log` —— 每次调用看到的消息列表。
- `llm.last_user_message` —— 方便直接取最后一条用户消息。

如果你只需要一次非流式响应，调用 `await llm.chat_complete(messages)` 即可，它会返回一个 `ChatResponse`。

### TestAgentBuilder — 轻量级 agent 组装

`testing/agent.py`。它会组装一个 `Controller` + `Executor` + `OutputRouter`，不用加载 YAML 配置，也不用跑完整的 `Agent.start()` 启动流程。适合单独测试 controller 循环和工具分发。

```python
from kohakuterrarium.testing import TestAgentBuilder

env = (
    TestAgentBuilder()
    .with_llm_script(["[/bash]@@command=echo hi\n[bash/]", "Done."])
    .with_builtin_tools(["bash", "read"])
    .with_system_prompt("You are a test agent.")
    .with_session("test_session")
    .build()
)

await env.inject("please echo")

assert env.llm.call_count >= 1
env.output.assert_text_contains("Done")
```

`env` 是一个 `TestAgentEnv`，暴露 `llm`、`output`、`controller`、`executor`、`registry`、`router`、`session`。`env.inject(text)` 会跑一轮：压入一条用户输入事件，从 scripted LLM 获取流式输出，解析工具或命令事件，通过 executor 分发工具，其余内容交给 `OutputRouter`。如果要注入原始事件，用 `env.inject_event(TriggerEvent(...))`。

Builder 方法（见 `testing/agent.py:19`）：

- `with_llm_script(list)` / `with_llm(ScriptedLLM)`
- `with_output(OutputRecorder)`
- `with_system_prompt(str)`
- `with_session(key)`
- `with_builtin_tools(list[str])` —— 通过 `get_builtin_tool` 解析
- `with_tool(instance)` —— 注册自定义工具
- `with_named_output(name, output)`
- `with_ephemeral(bool)`

### OutputRecorder — 供断言使用的捕获器

`testing/output.py`。这是 `BaseOutputModule` 的子类，会记录每次写入、每个流式 chunk 和每条 activity 通知。

```python
recorder = OutputRecorder()
await recorder.write("final text")
await recorder.write_stream("chunk1")
await recorder.write_stream("chunk2")
recorder.on_activity("tool_start", "[bash] job_123")

assert recorder.all_text == "chunk1chunk2final text"
assert recorder.stream_text == "chunk1chunk2"
assert recorder.writes == ["final text"]
recorder.assert_text_contains("chunk1")
recorder.assert_activity_count("tool_start", 1)
```

状态会分别记录在 `writes`、`streams`、`activities`、`processing_starts`、`processing_ends` 里。`reset()` 会在轮次之间清空 writes 和 streams（由 `OutputRouter` 调用）；`clear_all()` 还会清空 activities 和生命周期计数。

断言辅助方法：`assert_no_text`、`assert_text_contains`、`assert_activity_count`。

### EventRecorder — 记录时序和顺序

`testing/events.py`。它会带上单调递增时间戳和 source 标签记录事件。

```python
er = EventRecorder()
er.record("tool_complete", "bash ok", source="tool")
er.record("channel_message", "hello", source="channel")

assert er.count == 2
er.assert_order("tool_complete", "channel_message")
er.assert_before("tool_complete", "channel_message")
```

当你关心的是某件事什么时候触发，而不是文本内容时，这个工具很好用。

## 约定

- **用 `ScriptedLLM`，不要用 provider 层 mock。** 不要 monkey-patch `httpx` 或 OpenAI SDK。scripted LLM 位于 `LLMProvider` 协议边界上，controller 就是在这里和它交互。
- **除非在测持久化，否则测试里不要用 session store。** 这套支架默认跳过 `SessionStore`。对调用 `kt run` 的 CLI 集成测试，传 `--no-session`（或等价参数）。
- **记得清理。** Pytest fixture 应该每个测试构造一个 agent，并在结束后拆掉。`TestAgentBuilder.build()` 会调用 `set_session`，它会写入模块级 registry。如果测试泄漏了 session key，就给 `with_session(...)` 用不同的 key，或者在 `yield` 风格的 fixture 里清理。
- **不要走真实网络。** 如果某个东西会去请求 HTTP 端点，就在传输层 mock，或者直接跳过这个测试。
- **异步标记。** 异步测试加上 `@pytest.mark.asyncio`。如果你想用隐式标记，在 `pyproject.toml` 里设置 `asyncio_mode = "auto"`。

## 测试该加到哪里

在 `tests/unit/` 下按 `src/` 的目录结构对应放置：

| 你改了什么 | 测试加到哪里 |
|-------------------------|------------------------------------|
| `core/agent.py`         | `tests/unit/test_phase5.py` 或新文件 |
| `core/controller.py`    | `tests/unit/test_phase3_4.py`      |
| `core/executor.py`      | `tests/unit/test_phase3_4.py`      |
| `parsing/`              | `tests/unit/test_phase2.py`        |
| `modules/subagent/`     | `tests/unit/test_phase6.py`        |
| `modules/trigger/`      | `tests/unit/test_phase7.py`        |
| `core/environment.py`   | `tests/unit/test_environment.py`   |
| `session/store.py`      | `tests/unit/test_session_store.py` |
| `session/resume.py`     | `tests/unit/test_session_resume.py`|
| `bootstrap/`            | `tests/unit/test_bootstrap.py`     |
| `terrarium/`            | `tests/unit/test_terrarium_modules.py` |

跨组件流程放到 `tests/integration/`：

- channels —— `test_channels.py`
- output routing —— `test_output_isolation.py`
- 完整流水线（controller → executor → output）—— `test_pipeline.py`

如果该子系统还没有对应的测试文件，就新建一个，并保持命名风格一致。

## 快速测试和集成测试

- **快速单元测试** 应该用 `TestAgentBuilder`（不做文件 I/O，不调用真实 LLM），并且明显少于一秒。大多数测试都该是这一类。
- **集成测试** 会一起覆盖两个或更多子系统，比如带真实 executor 和真实工具的 controller 反馈循环。它们可以访问文件系统，也可以用真实的 session store，但仍应在个位数秒内结束。
- **手动 / 慢速测试**（真实 LLM 调用、长时间运行的 agent）不该放进默认测试套件。给它们加 `@pytest.mark.slow`，或者放到 `tests/manual/`。

## Lint 和格式化

提交前运行：

```bash
python -m black src/ tests/
python -m ruff check src/ tests/
python -m isort src/ tests/
```

Ruff 配置在 `pyproject.toml`。`[dev]` extra 会安装这三者。导入顺序遵循 [CLAUDE.md（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/CLAUDE.md)：内置模块、第三方模块、`kohakuterrarium.*`，组内按字母顺序，`import` 在 `from` 前，较短的点分路径排在较长路径前。

## 实现后的检查清单

对照 [CLAUDE.md（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/CLAUDE.md) 的 §Post-impl tasks：

1. 不要在函数内导入，除非是可选依赖，或者为了处理初始化顺序问题而有意做延迟加载。
2. Black + ruff + isort 全部通过。
3. 新行为要有测试。
4. 提交按逻辑拆分。除非有人要求，不要推送草稿提交。
