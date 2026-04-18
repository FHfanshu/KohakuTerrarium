# 边界

在 KohakuTerrarium 里，creature 抽象是 agent 的默认形态。
但它不是硬规矩。这个页面整理了两类情况：什么时候该跳出这套默认形态，什么时候这个框架本身就不适合你。

## 这个抽象只是默认，不是紧身衣

大多数 creature 都会同时出现六个模块：Controller、Input、Trigger、Tool、Sub-agent、Output。
但它们彼此独立，缺哪一块都可以：

- **没有 input。** `input: { type: none }`。cron creature、只收 webhook 的接收器、后台监控，这些都不需要用户输入。
- **没有 trigger。** 纯请求/响应式的聊天 creature，不靠任何环境事件唤醒，也完全没问题。
- **没有 tool。** 只负责回应的专用 creature，比如摘要、格式整理、翻译，可以一个工具都不用。LLM 自己也能做不少事。
- **没有 sub-agent。** 任务很短、从不委派的 creature，很常见。
- **没有 output。** 也有只做副作用的 creature。比如一个 creature 的唯一任务就是写入外部数据库，那它不需要 sink。
- **没有 memory / compaction / session。** 这种情况可以用 `--no-session` 和 `compact.enabled: false`。

框架并不偏爱六模块齐全的形态。只是当你想这么配时，它让这件事变得很便宜。

## 这个框架会主动拐弯用自己的抽象

这不是漏洞，本来就是设计的一部分。

**例子：channel。** channel 不是从 chat-bot → agent 那条推导线里长出来的。它是为多智能体场景引入的通信层。最简单的实现方式是：一个 tool 写消息；消息到了以后，一个 trigger 被触发。这样一来，一个概念会同时跨两个模块。没关系，这正是最自然的做法。硬要再造一个新原语，换不来什么。

**例子：root agent。** root 可以理解成“一个带有特定工具集和特定监听接线方式的 creature”。从结构上看，它和别的 creature 没区别；但从概念上看，它所在的位置确实重要。我们把它单独叫出来，是因为这样说有用，不是因为框架强制区分了它。

框架里的这些抽象，是拿来帮助思考的，不是墙。

## 什么情况下 KohakuTerrarium 合适

- 你的 agent 系统需求**还在变，或者根本没定下来**。你现在还不知道，下一轮迭代之后，哪些 tool、trigger、prompt 还能留下来。如果你做的东西还会继续变形，框架就值。
- 你想**试一种新的 agent 设计**——比如新的工具组合、触发方式，或者新的 sub-agent 结构——但不想把底层再重做一遍。
- 你想要**开箱即用、但可以改的 creature**。`kt-defaults` 能给你一个起点；继承一下，换掉几个模块，就行。
- 你想把 **agent 行为嵌进现有 Python 代码**里，而不是单独跑一个服务。
- 你想要一个**能复用零件的框架**，方便在团队之间或不同项目之间共享 creature、plugin、tool 和 preset 这类东西。

## 什么情况下它不合适

- 你已经**满意现在在用的 agent 产品**，而且需求也**很稳定**。如果 Claude Code、OpenClaw，或者你们内部现成的工具已经够用，而且你也不觉得需求会变，那迁过去只会增加切换成本，得不偿失。
- 你的**心智模型和这个框架对不上**。如果你理解 agent 的方式根本映射不到 controller / tools / triggers / sub-agents / channels 这一套上，硬套只会更糟。那就用别的，或者自己写另一套框架。
- 你的负载对**极低延迟**有硬要求，比如单次操作必须压到 50 ms 以下。KohakuTerrarium 优先的是正确性和灵活性；asyncio 开销、事件队列、output router、session 持久化，都会带来一点成本。多数时候没事，但有时就是不行。
- 你就是**不想用它**。这也完全算理由。一个框架不该出现在维护者本来就讨厌它的代码库里。

## 把这页当成一种许可

概念文档开头通常在回答“这是什么？”
收尾时该问的是：“这是不是适合我？”
如果上面那些**不合适**的情况说的就是你，那最对的做法就是去用别的，或者干脆什么都不用。这不算框架失败。
如果你更接近**合适**那一边，后面的文档就是写给你的。

## 另见

- [Why KohakuTerrarium](/concepts/foundations/why-kohakuterrarium.md)（英文）——解释这个框架为什么会这样设计。
- [What is an agent](/concepts/foundations/what-is-an-agent.md)（英文）——这页偏离的，就是那套标准推导。
- [Patterns](/concepts/patterns.md)（英文）——一些模块组合方式会故意打破“一个模块只做一件事”的直觉。
- [ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md)——目前还粗糙的地方，后面准备怎么处理。
