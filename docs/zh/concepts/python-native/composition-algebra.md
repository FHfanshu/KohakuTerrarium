# 组合代数

## 它是什么

当 agent 变成 Python 里的值，接下来你多半会想把它们串起来。**组合代数**就是一小组操作符和 combinator，用来把 agent（还有任何 async callable）当成可以拼接的单元：

- `a >> b` — 顺序执行（`a` 的输出会变成 `b` 的输入）
- `a & b` — 并行执行（两边一起跑，返回 `[result_a, result_b]`）
- `a | b` — fallback（如果 `a` 抛异常，就试 `b`）
- `a * N` — retry（失败时最多额外重试 `N` 次）
- `pipeline.iterate(stream)` — 把整条 pipeline 应用到 async iterable 的每个元素上；如果你想做循环，也可以把输出再喂回输入

不管怎么组合，最后拿到的都是一个 `BaseRunnable`，所以还能继续往下拼。

## 为什么会有这个

creature 里的 controller 本来就是个 loop。但有些 loop，你会想放在 creature 外面。比如 writer 和 reviewer 来回改，直到通过；几个 agent 并行回答，再挑一个最好的；或者跨 provider 做 retry 和 fallback。

这些东西直接用 `asyncio.gather` 和 `try/except` 当然写得出来，就是调用的地方会变得很碎。

这套操作符本质上只是 asyncio 上面的一层语法糖。没有新的执行模型，也没藏什么魔法。它只是让“把两个 agent 组合起来”这件事，看起来像“两个数相加”一样顺手。

## 它是怎么定义的

这里的协议是 `BaseRunnable.run(input) -> Any`（异步）。只要实现了这个方法，就能参与组合。

这些操作符分别对应：

- `__rshift__` 把两边包成 `Sequence`（会自动拍平嵌套的 sequence；如果右边是 dict，会变成 `Router`）。
- `__and__` 包成 `Product`；`run(x)` 会对所有分支做 `asyncio.gather`，并把 `x` 广播给每个分支当输入。
- `__or__` 包成 `Fallback`；一旦抛异常，就往后继续试。
- `__mul__` 包成 `Retry`；抛异常时最多重跑 N 次。

另外还有几种 combinator：

- `Pure(value)` — 包一层普通值或 callable；忽略输入。
- `Router(routes)` — 输入是 `{key: value}` 时，分发给对应的 runnable。
- `.map(fn)` — 先变换输入（`contramap`）。
- `.contramap(fn)` — 再变换输出。
- `.fails_when(pred)` — 如果谓词命中就主动抛错；和 `|` 搭起来很好用。

agent factory 有两种：

- `agent(config)` — 把持久化 agent 包成 runnable。多次调用之间会累积对话上下文。
- `factory(config)` — 每次调用都新建一个 agent；不保留持久状态。

## 它是怎么实现的

`compose/core.py` 放基础协议和 combinator 类。`compose/agent.py` 负责把 agent 包成 runnable。`compose/effects.py` 是可选的，用来记录 pipeline 里的副作用。

agent factory 的 wrapper 会把生命周期那点样板代码收掉：进入和退出时启动 / 停止底层 `Agent`，然后通过 `inject_input` 把输入送进去，再把输出收回来。

## 一个实际例子

```python
import asyncio
from kohakuterrarium.compose import agent, factory
from kohakuterrarium.core.config import load_agent_config

def make_agent(name, prompt):
    c = load_agent_config("@kt-biome/creatures/general")
    c.name, c.system_prompt, c.tools, c.subagents = name, prompt, [], []
    return c

async def main():
    async with await agent(make_agent("writer", "You are a writer.")) as writer, \
               await agent(make_agent("reviewer", "You are a strict reviewer. Say APPROVED if good.")) as reviewer:

        pipeline = writer >> (lambda text: f"Review this:\n{text}") >> reviewer

        async for feedback in pipeline.iterate("Write a haiku about coding"):
            print(f"Reviewer: {feedback[:100]}")
            if "APPROVED" in feedback:
                break

    fast = factory(make_agent("fast", "Answer concisely."))
    deep = factory(make_agent("deep", "Answer thoroughly."))
    safe = (fast & deep) >> (lambda results: max(results, key=len))
    safe_with_retry = (safe * 2) | fast
    print(await safe_with_retry("What is recursion?"))

asyncio.run(main())
```

这里有两个 agent、持久对话、一个反馈 loop，再加上一个带 fallback 和 retry 的并行组合。写法还是普通 Python。

## 你可以拿它做什么

- **审阅 loop。** `writer >> reviewer` 配上 `.iterate(...)`，一直跑到某个条件满足，不用另写编排代码。
- **组合回答。** `(fast & deep) >> pick_best`，让两个 agent 并行跑，再把结果合起来。
- **fallback 链。** 先试便宜的 provider，失败了再切到更强的。
- **处理暂时性失败。** 给任何 runnable 套一层 `* N`。
- **流式 pipeline。** `.iterate(async_generator)` 会让异步生成器里的每个元素都走完整条 pipeline。

## 别被它框住

组合代数不是必需的。大多数嵌入场景里，creature config 加上 `AgentSession` 就够了。只有在你真想不靠 terrarium，直接用 Python 写多 agent 编排的时候，这套操作符才特别顺手。

状态说明：这套代数已经挺有用，但还在继续调整。操作符后面可能会增加，也可能会简化，具体看反馈。拿它写内部 pipeline 没什么问题；如果要上生产，先把它当成 early-stable 比较稳妥。

## 另见

- [Agent as a Python object](agent-as-python-object.md) —— 这篇的基础。
- [Patterns](../patterns.md) —— 组合代数和嵌入式 agent 混着用时的一些模式。
- [组合](../../composition.md) —— 面向任务的用法。
- [Python 参考：`kohakuterrarium.compose`](../../reference/python.md) —— 完整 API。
