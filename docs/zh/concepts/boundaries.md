# 边界

在 KohakuTerrarium 里，creature 是 agent 的默认形态。
但它不是死规矩。这一页讲两件事：什么时候该跳出这套默认形态，什么时候这个框架压根不适合你。

## 这个抽象只是默认，不是束身衣

大多数 creature 会同时带上六个模块：Controller、Input、Trigger、Tool、Sub-agent、Output。
但这六块是拆开的，少哪块都行：

- **没有 input。** `input: { type: none }`。cron creature、只收 webhook 的接收器、后台监控，都不需要用户打字。
- **没有 trigger。** 纯 request/response 的聊天 creature，不靠环境事件唤醒，也照样能用。
- **没有 tool。** 只负责输出结果的 creature，比如 summariser、formatter、translator，可以一个 tool 都不用。LLM 本身就能干不少活。
- **没有 sub-agent。** 不做委派、任务也短的 creature，很常见。
- **没有 output。** 也有只做副作用的 creature。比如它唯一的工作就是往外部数据库写数据，那就不需要 sink。
- **没有 memory / compaction / session。** 这种情况可以用 `--no-session` 和 `compact.enabled: false`。

框架并不偏爱六模块配齐的形态。只是你想这么搭的时候，它做起来很省事。

## 框架也会绕开自己的抽象

这不是漏洞，本来就是这样设计的。

**例子：channel。** channel 不是从 chat-bot → agent 那条主线里直接讲出来的。它是为了 multi-agent 场景补上的通信层。最简单的实现就是：一个 tool 写消息，消息一到，trigger 就触发。一个概念横跨两个模块没关系，这样反而更顺。硬要再造一个新原语，意义不大。

**例子：root agent。** root 可以理解成“一个带着特定 toolset 和特定监听接线方式的 creature”。从结构上看，它跟别的 creature 没差别；但从概念上看，它站的位置就是不一样。我们把它单独拎出来说，是因为这样更好理解，不是因为框架硬性规定了一个特殊类型。

这些抽象是帮你思考的，不是拿来砌墙的。

## 什么情况下 KohakuTerrarium 合适

- 你的 agent 系统需求**还在变，或者根本没定下来**。你现在说不准下一轮之后，哪些 tool、trigger、prompt 还会留下来。东西还在变形，用框架通常划算。
- 你想**试新的 agent 设计**，比如新的 tool 组合、trigger 组合，或者新的 sub-agent 结构，但不想每次都把底层重搭一遍。
- 你想要**开箱就能用、但也能改的 creature**。`kt-biome` 可以当起点；继承一下，换几个模块，就够了。
- 你想把 **agent 行为嵌进现有 Python 代码**，而不是另外跑一个服务。
- 你想要一个**方便复用零件的框架**，能在团队之间或不同项目之间共享 creature、plugin、tool、preset 这些东西。

## 什么情况下它不合适

- 你已经**满意手头在用的 agent 产品**，而且需求也**比较稳定**。如果 Claude Code、OpenClaw，或者你们内部现成工具已经够用，之后大概也不会大改，那迁过来只是多一笔切换成本。
- 你的**理解方式跟这个框架对不上**。如果你脑子里那套 agent 模型，根本套不到 controller / tools / triggers / sub-agents / channels 这一套上，那就别硬上。换别的，或者自己写一套更合适的。
- 你的负载对**超低延迟**有硬要求，比如单次操作得压到 50 ms 以下。KohakuTerrarium 优先的是正确性和灵活性；asyncio 开销、事件队列、output router、session 持久化，都会带来一点成本。大多数场景没问题，但有些场景就是不行。
- 你就是**不想用它**。这也完全算理由。一个框架不该待在维护者本来就烦它的代码库里。

## 把这页当成一种许可

概念文档开头常在回答“这是什么？”。
到结尾，真正该问的是：“这是不是适合我？”

如果上面那些**不合适**的情况说的就是你，那最好的做法就是用别的，或者干脆什么都不用。这不算框架失败。
如果你更接近**合适**那一边，后面的文档就是写给你的。

## 另见

- [Why KohakuTerrarium](foundations/why-kohakuterrarium.md) —— 这个框架为什么会这样设计。
- [What is an agent](foundations/what-is-an-agent.md) —— 这页讲的是那条主线。这里说的偏离，就是偏离它。
- [模式](patterns.md) —— 有些模块组合会故意打破“一个模块只做一件事”的直觉。
- [ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md) —— 现在还比较粗糙的地方，以及后面准备怎么改。
