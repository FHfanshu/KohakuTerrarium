# 组合

如果你想直接用 Python 写多 agent 编排，又不想先搭一个 terrarium，这一页就是讲这个的。

`compose` 代数把 agent 和异步可调用对象都当成可组合单元。四个操作符（`>>`、`&`、`|`、`*`）分别对应串行、并行、失败回退和重试。每一步都会返回一个 `BaseRunnable`，可以继续往下拼。

概念先看：[composition algebra](/concepts/python-native/composition-algebra.md)（英文）、[agent as a Python object](/concepts/python-native/agent-as-python-object.md)（英文）。

你要把循环放在 creature 外面时，用这套东西最顺手：比如 writer ↔ reviewer 一直跑到通过，或者并行 ensemble，或者从便宜模型回退到贵模型。要做共享 channel 的横向多 agent 系统，用 [Terrarium](/guides/terrariums.md)（英文）。

## 操作符

| 操作 | 含义 |
|---|---|
| `a >> b` | 串行：`b(a(x))`。会自动展平。右侧如果是 dict，会转成 `Router`。 |
| `a & b` | 并行：`asyncio.gather(a(x), b(x))`。返回 list。 |
| `a \| b` | 回退：如果 `a` 抛异常，就试 `b`。 |
| `a * N` | 遇到异常时，额外重试 `a` 最多 `N` 次。 |

优先级：`*` > `|` > `&` > `>>`。

组合器：

- `Pure(fn_or_value)` —— 包一层普通可调用对象。
- `.map(fn)` —— 对输出做后处理。
- `.contramap(fn)` —— 对输入做预处理。
- `.fails_when(pred)` —— 谓词命中时抛异常（可和 `|` 配合）。
- `pipeline.iterate(stream)` —— 把 pipeline 依次应用到异步可迭代对象的每个元素上。

## `agent` 和 `factory`

有两种 agent 包装器：

- `agent(config_or_path)` —— **持久化** agent（异步上下文管理器）。多次调用会累积对话上下文，适合一段持续交互。
- `factory(config)` —— **按调用创建** 的 agent。每次调用都会新建一个 agent，不保留状态，适合无状态 worker。

```python
from kohakuterrarium.compose import agent, factory

async with await agent("@kt-defaults/creatures/swe") as swe:
    r1 = await swe("Read the repo.")
    r2 = await swe("Now fix the auth bug.")   # same conversation

coder = factory(some_config)
r1 = await coder("Task 1")                    # fresh agent
r2 = await coder("Task 2")                    # another fresh agent
```

## writer ↔ reviewer 循环

让两个 agent 一直跑，直到 reviewer 通过：

```python
import asyncio
from kohakuterrarium.compose import agent
from kohakuterrarium.core.config import load_agent_config

def make(name, prompt):
    c = load_agent_config("@kt-defaults/creatures/general")
    c.name, c.system_prompt = name, prompt
    c.tools, c.subagents = [], []
    return c

async def main():
    async with await agent(make("writer", "You are a writer.")) as writer, \
               await agent(make("reviewer", "Strict reviewer. Say APPROVED when good.")) as reviewer:

        pipeline = writer >> (lambda text: f"Review this:\n{text}") >> reviewer

        async for feedback in pipeline.iterate("Write a haiku about coding."):
            print(f"Reviewer: {feedback[:120]}")
            if "APPROVED" in feedback:
                break

asyncio.run(main())
```

`.iterate()` 会把 pipeline 的输出再喂回去，作为下一轮输入，所以它返回的是一个异步流，可以直接用原生 `async for` 来跑。

## 并行 ensemble，再挑一个最好的

三个 agent 并行跑，最后保留最长的回答：

```python
from kohakuterrarium.compose import factory

fast = factory(make("fast", "Answer concisely."))
deep = factory(make("deep", "Answer thoroughly."))
creative = factory(make("creative", "Answer imaginatively."))

ensemble = (fast & deep & creative) >> (lambda results: max(results, key=len))
best = await ensemble("What is recursion?")
```

`&` 底层走的是 `asyncio.gather`，所以三个分支会并发执行。总耗时看最慢的那个，不是三个加起来。

## 重试加回退链

先让昂贵的 expert 试两次，不行再退回便宜的 generalist：

```python
safe = (expert * 2) | generalist
result = await safe("Explain JSON-RPC.")
```

也可以和基于错误条件的回退配合：

```python
cheap = fast.fails_when(lambda r: len(r) < 50)
pipeline = cheap | deep            # if fast returns < 50 chars, try deep
```

## 路由

`>>` 右边如果是 dict，会变成一个 `Router`：

```python
router = classifier >> {
    "code":   coder,
    "math":   solver,
    "prose":  writer,
}
```

上游步骤应该输出一个 dict，格式是 `{classifier_key: payload}`；路由器会选出匹配的分支。常见用法就是“先分类，再分发”。

## 混用 agent 和函数

普通可调用对象会自动用 `Pure` 包起来：

```python
pipeline = (
    writer
    >> str.strip                      # zero-arg callable on the output
    >> (lambda t: {"text": t})        # lambda
    >> reviewer
    >> json.loads                     # parse reviewer's JSON response
)
```

同步和异步可调用对象都能用；如果是异步函数，会自动 `await`。

## 带副作用的日志

```python
from kohakuterrarium.compose.effects import Effects

effects = Effects()
logged = effects.wrap(pipeline, on_call=lambda step, x, y: print(f"{step}: {x!r} -> {y!r}"))
result = await logged("input")
```

想看 pipeline 怎么流转、又不想改 pipeline 本身时，这个很好用。

## 什么时候改用 terrarium

下面这些情况更适合 terrarium：

- creature 需要**持续运行**，按自己的节奏响应消息。
- 你需要热插拔 creature，或者接外部观测能力。
- 多个 creature 共享同一个工作空间（scratchpad、channel），并且需要 `Environment` 隔离。

下面这些情况更适合 composition：

- 你的应用本身就是编排器，按需调用 agent。
- pipeline 生命周期很短，通常跟着一次请求走，不是长期运行。
- 你想直接用原生 Python 控制流（`for`、`if`、`try`、`gather`）。

## 排错

- **重复使用 `agent()` 时报错。** 它是异步上下文管理器，要放在 `async with` 里面用。
- **Pipeline 意外返回了 list。** 说明你某处用了 `&`；它的结果就是 list。加一个 `>> (lambda results: ...)` 收一下。
- **Retry 没有重试。** `* N` 只会在抛异常时触发。想把“看起来不对但没报错”的结果也当失败，用 `.fails_when(pred)` 转成异常。
- **步骤之间类型对不上。** 前一步的输出就是后一步的输入。中间插一个 `Pure` 函数（或者 lambda）做适配。

## 另见

- [Programmatic Usage](/guides/programmatic-usage.md)（英文）—— 底层的 `Agent` / `AgentSession` API。
- [Concepts / composition algebra](/concepts/python-native/composition-algebra.md)（英文）—— 设计原因。
- [Reference / Python API](/reference/python.md)（英文）—— `compose.core`、`compose.agent`、操作符签名。
- [examples/code/](https://github.com/Kohaku-Lab/KohakuTerrarium/tree/main/examples/code)（英文）—— `review_loop.py`、`ensemble_voting.py`、`debate_arena.py`、`smart_router.py`、`pipeline_transforms.py`。
