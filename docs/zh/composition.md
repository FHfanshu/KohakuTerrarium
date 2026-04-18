# 组合

如果你想直接用 Python 编排多 agent，又不想先搭一个 terrarium，就看这一页。

`compose` 这套组合代数，把 agent 和异步可调用对象都当成可拼接的单元。四个操作符：`>>`、`&`、`|`、`*`，分别表示串行、并行、回退和重试。每一步都会返回一个 `BaseRunnable`，所以可以一直往后接。

先补概念可以看：[组合代数](/zh/concepts/python-native/composition-algebra.md)、[把 agent 当成 Python 对象](/zh/concepts/python-native/agent-as-python-object.md)。

什么时候适合用这个？你想把循环写在 creature 外面时，比如 writer ↔ reviewer 一直跑到通过，或者并行跑一组 agent，再从便宜模型一路回退到贵模型。要做共享 channel 的横向多 agent 系统，就用 [Terrarium](/zh/guides/terrariums.md)。

## 操作符

| 操作 | 含义 |
|---|---|
| `a >> b` | 串行：`b(a(x))`。会自动展平。右边如果是 dict，会变成 `Router`。 |
| `a & b` | 并行：`asyncio.gather(a(x), b(x))`。返回一个 list。 |
| `a \| b` | 回退：如果 `a` 抛异常，就改试 `b`。 |
| `a * N` | 遇到异常时，额外重试 `a`，最多 `N` 次。 |

优先级：`*` > `|` > `&` > `>>`。

组合器：

- `Pure(fn_or_value)` —— 给普通可调用对象包一层。
- `.map(fn)` —— 处理输出。
- `.contramap(fn)` —— 先处理输入。
- `.fails_when(pred)` —— 谓词命中时抛异常，常和 `|` 一起用。
- `pipeline.iterate(stream)` —— 把 pipeline 应用到异步可迭代对象的每个元素上。

## `agent` 和 `factory`

有两种 agent 包装方式：

- `agent(config_or_path)` —— **持久型** agent（异步上下文管理器）。多次调用会累积对话上下文，适合一段持续交互。
- `factory(config)` —— **按次创建** 的 agent。每次调用都会新建一个 agent，不继承上一次状态，适合无状态 worker。

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

让两个 agent 反复跑，直到 reviewer 通过：

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

`.iterate()` 会把 pipeline 的输出再喂回去，作为下一轮输入，所以你拿到的是一个异步流，可以直接用原生 `async for` 来跑。

## 并行 ensemble，再挑一个最好的

让三个 agent 并行跑，最后留最长的回答：

```python
from kohakuterrarium.compose import factory

fast = factory(make("fast", "Answer concisely."))
deep = factory(make("deep", "Answer thoroughly."))
creative = factory(make("creative", "Answer imaginatively."))

ensemble = (fast & deep & creative) >> (lambda results: max(results, key=len))
best = await ensemble("What is recursion?")
```

`&` 底层用的是 `asyncio.gather`，所以三个分支会同时执行。总耗时取决于最慢的那个，不是三个时间相加。

## 重试 + 回退链

先让昂贵的 expert 试两次，不行再退回便宜的 generalist：

```python
safe = (expert * 2) | generalist
result = await safe("Explain JSON-RPC.")
```

也可以配合“命中某种结果就算失败”的回退：

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

上游步骤应该输出一个 dict，格式是 `{classifier_key: payload}`；路由器会选对应的分支。这就是典型的“先分类，再分发”。

## 混用 agent 和函数

普通可调用对象会自动包成 `Pure`：

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

想看 pipeline 里每一步怎么流动、又不想改 pipeline 本身时，这个办法很省事。

## 什么时候该用 terrarium

下面这些情况，更适合用 terrarium：

- creature 需要**持续运行**，按自己的节奏处理消息。
- 你需要热插拔 creature，或者接外部观测能力。
- 多个 creature 共享同一个工作空间（scratchpad、channel），而且需要 `Environment` 隔离。

下面这些情况，更适合用 composition：

- 你的应用本身就是编排器，按需调用 agent。
- pipeline 生命周期很短，通常只跟着一次请求走，不会长期运行。
- 你想直接用原生 Python 控制流，比如 `for`、`if`、`try`、`gather`。

## 排错

- **重复使用 `agent()` 时会报错。** 它是异步上下文管理器，要放在 `async with` 里用。
- **Pipeline 怎么突然返回 list 了。** 说明你 somewhere 用了 `&`；它的结果就是 list。后面加一个 `>> (lambda results: ...)` 收一下。
- **Retry 没生效。** `* N` 只会在抛异常时触发。要把“看着不对但没报错”的结果也算失败，可以用 `.fails_when(pred)` 把它转成异常。
- **步骤之间类型对不上。** 前一步的输出就是后一步的输入。中间插一个 `Pure` 函数，或者一个 lambda，做适配就行。

## 另见

- [编程式用法](/zh/guides/programmatic-usage.md) —— 底层的 `Agent` / `AgentSession` API。
- [概念 / 组合代数](/zh/concepts/python-native/composition-algebra.md) —— 设计思路。
- [参考 / Python API](/zh/reference/python.md) —— `compose.core`、`compose.agent`、操作符签名。
- [examples/code/](https://github.com/Kohaku-Lab/KohakuTerrarium/tree/main/examples/code) —— `review_loop.py`、`ensemble_voting.py`、`debate_arena.py`、`smart_router.py`、`pipeline_transforms.py`。
