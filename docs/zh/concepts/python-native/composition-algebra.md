# 组合代数

## 它是什么

当 agent 成了 Python 值，下一步通常就是把它们接起来。**组合代数**提供了一小组操作符和组合子，把 agent（以及任何异步可调用对象）都当成可组合的单元：

- `a >> b` — 顺序执行（`a` 的输出变成 `b` 的输入）
- `a & b` — 并行执行（两边同时运行，返回 `[result_a, result_b]`）
- `a | b` — 回退（如果 `a` 抛异常，就试 `b`）
- `a * N` — 重试（失败时最多再试 `N` 次）
- `pipeline.iterate(stream)` — 把管道应用到异步可迭代对象的每个元素上；如果你想做循环，也可以把输出再喂回输入

这些操作最后都会返回一个 `BaseRunnable`，所以你可以继续往下组合。

## 为什么会有它

creature 里的 controller 本身就是个循环。但有时你想把循环放在 creature 外面：writer ↔ reviewer 反复迭代直到通过，多个 agent 并行回答再选最好的，或者在不同 provider 之间做重试加回退。

这些事情直接用 `asyncio.gather` 和 `try/except` 当然也能写，只是调用点会变乱。

这些操作符本质上是给 asyncio 加了一层顺手的语法糖。它们没有引入新的执行模型，只是让“组合两个 agent”这件事，读起来像“两个数相加”一样直接。

## 我们怎么定义它

`BaseRunnable.run(input) -> Any`（异步）是这里的协议。任何实现了这个方法的对象都可以参与组合。

这些操作符分别对应：

- `__rshift__` 把两边包成 `Sequence`（会自动拍平嵌套的 sequence；如果右侧是 dict，会变成 `Router`）。
- `__and__` 包成 `Product`；`run(x)` 会对所有分支执行 `asyncio.gather`，并把 `x` 广播为每个分支的输入。
- `__or__` 包成 `Fallback`；遇到异常就往后接着试。
- `__mul__` 包成 `Retry`；遇到异常时最多重跑 N 次。

另外还有一些组合子：

- `Pure(value)` — 包装普通值或可调用对象；忽略输入。
- `Router(routes)` — 输入是 `{key: value}` 时，分发到对应的 runnable。
- `.map(fn)` — 预先变换输入（`contramap`）。
- `.contramap(fn)` — 后处理输出。
- `.fails_when(pred)` — 谓词命中时主动抛错；和 `|` 一起用很方便。

agent 工厂有两种：

- `agent(config)` — 把持久化 agent 包成 runnable。对话上下文会在多次调用之间累积。
- `factory(config)` — 每次调用都新建一个 agent；不保留持久状态。

## 我们怎么实现它

`compose/core.py` 放基础协议和各个组合子类。`compose/agent.py` 负责把 agent 包装成 runnable。`compose/effects.py` 是可选的，用来记录管道里的副作用。

agent-factory 的包装器会处理生命周期这部分样板代码：进入和退出时启动 / 停止底层 `Agent`，并通过 `inject_input` 传入输入，再收集输出。

## 一个实际例子

```python
import asyncio
from kohakuterrarium.compose import agent, factory
from kohakuterrarium.core.config import load_agent_config

def make_agent(name, prompt):
    c = load_agent_config("@kt-defaults/creatures/general")
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

这里有两个 agent、持久对话、一个反馈循环，还有一个带回退和重试的并行组合，写法都还是普通 Python。

## 你可以拿它做什么

- **审阅循环。** `writer >> reviewer` 再配合 `.iterate(...)`，一直跑到某个条件满足，不用额外写编排代码。
- **组合回答。** `(fast & deep) >> pick_best`，让两个 agent 并行运行，再把结果合起来。
- **回退链。** 先试便宜的 provider，失败了再退到更强的。
- **处理临时性失败。** 给任何 runnable 套一层 `* N`。
- **流式管道。** `.iterate(async_generator)` 会把异步生成器里的每个元素都跑完整条管道。

## 别被它绑住

组合代数不是必需的。对大多数嵌入式使用场景，creature 配置加上 `AgentSession` 已经够了。只有当你真的想在不启用 terrarium 的情况下，直接用 Python 写多 agent 编排时，这套操作符才会派上用场。

状态说明：这套代数已经能用，但还在继续调整。具体的操作符集合后面可能会增加，也可能会收缩，取决于反馈。内部管道可以放心用；如果要上生产，最好把它看作早期稳定。

## 另见

- [Agent as a Python object](/concepts/python-native/agent-as-python-object.md)（英文）— 这篇的基础。
- [Patterns](/concepts/patterns.md)（英文）— 组合代数和嵌入式 agent 一起使用时的常见模式。
- [guides/composition.md](/guides/composition.md)（英文）— 面向任务的用法。
- [reference/python.md — kohakuterrarium.compose](/reference/python.md)（英文）— 完整 API。
