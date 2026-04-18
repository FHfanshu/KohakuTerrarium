# 测试

测试都在 `tests/` 下面，分成单元测试 `tests/unit/` 和集成测试 `tests/integration/`。另外 `src/kohakuterrarium/testing/` 里还有一套现成的测试工具，方便你用假的 LLM 搭 agent。

## 运行测试

```bash
pytest                                    # 全量测试
pytest tests/unit                         # 只跑单元测试
pytest tests/integration                  # 只跑集成测试
pytest -k channel                         # 名字里带 "channel" 的都跑
pytest tests/unit/test_phase3_4.py::test_executor_parallel
pytest -x                                 # 遇到第一个失败就停
pytest --no-header -q                     # 输出更安静
```

测试要跑在完整的 asyncio 环境里。异步测试函数用 `pytest-asyncio`（`@pytest.mark.asyncio`）。别在测试里手写 `asyncio.run()`，让插件自己管 event loop。

## 测试 harness

`src/kohakuterrarium/testing/` 常用的东西有这几个，直接从包根导入：

```python
from kohakuterrarium.testing import (
    ScriptedLLM, ScriptEntry,
    OutputRecorder,
    EventRecorder, RecordedEvent,
    TestAgentBuilder,
)
```

### ScriptedLLM — 可控的 LLM mock

在 `testing/llm.py`。它实现了 `LLMProvider` 协议，但不会真的去调 API。你给它一串响应，它就按顺序往外吐。

```python
# 最简单：直接给字符串
llm = ScriptedLLM(["Hello.", "I'll use a tool.", "Done."])

# 复杂一点：用 ScriptEntry，支持按 match 选择，也能控制流式输出。
# tool call 语法必须和 parser 的 tool_format 一致，默认是
# bracket: [/name]@@arg=value\nbody[name/]
llm = ScriptedLLM([
    ScriptEntry("I'll search.", match="find"),   # 只有最后一条用户消息里包含 "find" 才会触发
    ScriptEntry("Sorry, can't.", match="help"),
    ScriptEntry("[/bash]@@command=echo hi\n[bash/]", chunk_size=5),
])
```

`ScriptEntry`（`testing/llm.py:12`）有这些字段：

- `response: str` — 完整文本，可以带框架格式的 tool call。
- `match: str | None` — 设了的话，只有最后一条用户消息里带这个子串才会用这条。
- `delay_per_chunk: float` — 每个 chunk 之间等多久。
- `chunk_size: int` — 每次 yield 多少个字符，默认 10。

跑完以后常看这几个：

- `llm.call_count`
- `llm.call_log` — 每次调用时看到的 message 列表
- `llm.last_user_message` — 最后一条用户消息

如果你只想要一个非流式响应，直接调：
`await llm.chat_complete(messages)`，它会返回 `ChatResponse`。

### TestAgentBuilder — 轻量装一个 agent

在 `testing/agent.py`。它会直接组一个 `Controller`、`Executor`、`OutputRouter`，不用加载 YAML，也不用跑完整的 `Agent.start()`。拿它单测 controller loop 和 tool dispatch 很省事。

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

`env` 是个 `TestAgentEnv`，里面有 `llm`、`output`、`controller`、`executor`、`registry`、`router`、`session`。`env.inject(text)` 会完整跑一轮：塞一个 user-input event，拿 scripted LLM 的流式输出，解析 tool/command event，把 tool 丢给 executor，其他内容交给 `OutputRouter`。如果你想直接喂原始事件，用 `env.inject_event(TriggerEvent(...))`。

Builder 方法见 `testing/agent.py:19`：

- `with_llm_script(list)` / `with_llm(ScriptedLLM)`
- `with_output(OutputRecorder)`
- `with_system_prompt(str)`
- `with_session(key)`
- `with_builtin_tools(list[str])` — 通过 `get_builtin_tool` 解析
- `with_tool(instance)` — 注册自定义 tool
- `with_named_output(name, output)`
- `with_ephemeral(bool)`

### OutputRecorder — 抓输出做断言

在 `testing/output.py`。它是 `BaseOutputModule` 的子类，会把每次 write、stream chunk、activity 通知都记下来。

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

它会分别记这些状态：`writes`、`streams`、`activities`、`processing_starts`、`processing_ends`。`reset()` 会在每轮之间清掉 writes 和 streams（`OutputRouter` 会调它）；`clear_all()` 会把 activities 和生命周期计数也一起清掉。

断言辅助方法有：`assert_no_text`、`assert_text_contains`、`assert_activity_count`。

### EventRecorder — 记时序

在 `testing/events.py`。它会带着单调递增时间戳和 source label 记录事件。

```python
er = EventRecorder()
er.record("tool_complete", "bash ok", source="tool")
er.record("channel_message", "hello", source="channel")

assert er.count == 2
er.assert_order("tool_complete", "channel_message")
er.assert_before("tool_complete", "channel_message")
```

适合那种你关心先后顺序，而不是具体文本的场景。

## 约定

- **用 `ScriptedLLM`，别去 mock provider 底层。** 不要 monkey-patch `httpx` 或 OpenAI SDK。`ScriptedLLM` 就卡在 `LLMProvider` 这一层，controller 也是在这里跟 LLM 打交道。
- **除非你就在测持久化，不然别带 session store。** harness 默认会跳过 `SessionStore`。如果是 `kt run` 的 CLI 集成测试，就传 `--no-session` 或等价参数。
- **记得清理。** Pytest fixture 最好一测一个 agent，用完就拆。`TestAgentBuilder.build()` 会调 `set_session`，会往模块级 registry 里写东西。要是 session key 泄漏了，就给 `with_session(...)` 换个 key，或者在 `yield` fixture 里清掉。
- **不要走真网络。** 只要有东西要打 HTTP，就在传输层 mock，或者直接跳过。
- **Async 标记别漏。** 异步测试记得加 `@pytest.mark.asyncio`。如果想省点事，也可以在 `pyproject.toml` 里设 `asyncio_mode = "auto"`。

## 测试该放哪

`tests/unit/` 基本按 `src/` 结构来放：

| 你改了什么 | 测试加到哪里 |
|---|---|
| `core/agent.py` | `tests/unit/test_phase5.py` 或新文件 |
| `core/controller.py` | `tests/unit/test_phase3_4.py` |
| `core/executor.py` | `tests/unit/test_phase3_4.py` |
| `parsing/` | `tests/unit/test_phase2.py` |
| `modules/subagent/` | `tests/unit/test_phase6.py` |
| `modules/trigger/` | `tests/unit/test_phase7.py` |
| `core/environment.py` | `tests/unit/test_environment.py` |
| `session/store.py` | `tests/unit/test_session_store.py` |
| `session/resume.py` | `tests/unit/test_session_resume.py` |
| `bootstrap/` | `tests/unit/test_bootstrap.py` |
| `terrarium/` | `tests/unit/test_terrarium_modules.py` |

跨组件流程放到 `tests/integration/`：

- channels — `test_channels.py`
- output routing — `test_output_isolation.py`
- 整条 pipeline（controller → executor → output）— `test_pipeline.py`

如果某个子系统还没有现成测试文件，就新建一个，命名风格照现有的来。

## 快测试和集成测试

- **快的单元测试** 用 `TestAgentBuilder`，别碰文件 I/O，别走真实 LLM，最好一秒内跑完。默认测试集应该以这种为主。
- **集成测试** 是把两个或更多子系统一起跑起来，比如 controller 的反馈循环配真实 executor 和真实 tools。可以碰文件系统，也可以用真的 session store，但最好还是控制在几秒内。
- **手动 / 慢测试**，比如真实 LLM 调用、长时间运行的 agent，不该进默认测试集。给它们打 `@pytest.mark.slow`，或者放进 `tests/manual/`。

## Lint 和格式化

提交前跑一遍：

```bash
python -m black src/ tests/
python -m ruff check src/ tests/
python -m isort src/ tests/
```

Ruff 配置在 `pyproject.toml`。`[dev]` extra 会把这三个都装上。import 排序跟 [CLAUDE.md](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/CLAUDE.md) 一致：先内建，再第三方，再 `kohakuterrarium.*`；组内按字母序；先 `import` 后 `from`；点路径短的排前面。

## 实现后检查清单

对照 [CLAUDE.md](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/CLAUDE.md) 里的 §Post-impl tasks：

1. 不要在函数里 import（可选依赖，或者为了处理初始化顺序故意做的 lazy loading 除外）。
2. Black、ruff、isort 都要干净。
3. 新行为要带测试。
4. commit 按逻辑拆。没人要求的话，别推草稿。
