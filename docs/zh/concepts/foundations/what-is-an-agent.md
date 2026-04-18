# 什么是 agent

在 KohakuTerrarium 里，agent 就是一个 **creature**。要明白 creature 为什么长这样，最简单的办法是从零一点点搭起来看。

## Stage 0 — Chat bot

```
    +-------+      +-----+      +--------+
    | Input | ---> | LLM | ---> | Output |
    +-------+      +-----+      +--------+
```

用户输入一句，模型回一句，然后把结果打印出来。这已经是对话式 AI 最简单的形态了。它会*说话*，但不会*做事*。

## Stage 1 — 加上 tools system

```
                 +--------------+
                 | Tools System |
                 +------+-------+
                        ^  |
                        |  v
    +-------+      +---------+      +--------+
    | Input | ---> |   LLM   | ---> | Output |
    +-------+      +---------+      +--------+
```

给 LLM 一个调用 tool 的能力，比如执行 shell 命令、改文件、搜网页。这样它就能动手了。到这一步，它已经不只是 chat bot，而是更接近 smolagent 或 swe-agent 语境里的 agent。

这已经很好用了，但限制也很明显：想让它做事，你还是得*手动给它发消息*。

## Stage 2 — 加上 trigger system

```
                                +--------------+
                           +--> | Tools System |
                           |    +--------------+
                           |           ^  |
                           |           |  v
    +-------+   +---------+v     +---------+      +--------+
    | Input |-->| Trigger |----->|   LLM   | ---> | Output |
    +-------+   | System  |      +---------+      +--------+
                +---------+
```

真正能用的 agent，不能每次都等用户来叫醒。`/loop`、后台任务结束、空闲检查、webhook、定时器，这些都可能让它该醒了。得有个东西盯着外部世界，在条件满足时去触发 controller，这个东西就是 **trigger**。

有了 trigger 之后你很快会发现，*用户输入本身其实也只是 trigger 的一种*。所以所谓 input，只是更通用的唤醒机制里的一个特例。Claude Code 和 OpenClaw 大致就在这个阶段。

## Stage 3 — 加上 sub-agent

```
                                +--------------+
                           +--> | Tools System |
                           |    +--------------+
                           |           ^  |
                           |           |  v
    +-------+   +---------+v     +---------+      +--------+
    | Input |-->| Trigger |----->|   LLM   | ---> | Output |
    +-------+   | System  |      +---------+      +--------+
                +---------+            ^  |
                                       |  v
                                 +--------------+
                                 |  Sub Agents  |
                                 +--------------+
```

context window 是有限的。一个长任务里如果有很多探索性的子步骤，而这些步骤全都塞进父级对话，很快就会把上下文预算吃光。

常见的做法是起一个 **sub-agent**：它是嵌套进去的 creature，用自己的上下文跑，最后只回传一个压缩过的结果，然后退出。还有一点很重要，从父级视角看，sub-agent *其实也就是一种 tool*——你调它，它给你返回结果。现在常见的 coding agent 基本都走到这一步了。

## 六模块 creature

把前面的东西合起来，就是这样：

| Module | Role |
|---|---|
| **Controller** | 推理循环。它从 LLM 流式接收内容，解析 tool 调用，再把它们派发出去。 |
| **Input** | 告诉 controller 该做什么，也就是某一种特定的 trigger。 |
| **Trigger** | 当外部世界要求它醒来时，负责触发 controller。 |
| **Tool** | agent 用来做事的东西。 |
| **Sub-agent** | 嵌套进去的 creature。从概念上说，它也算一种 tool。 |
| **Output** | agent 怎么把结果回给外部世界。 |

**creature** 就是这六个模块放在一起。它是 KohakuTerrarium 里的核心抽象，后面的 guide、reference，还有其他 concept 文档，说到底都围着它转。

这里先补一句，免得你看到别处时犯嘀咕：有些 README 或 guide 会说“有五种可扩展模块类型”。那个说法指的是用户可以替换的五种：Input、Trigger、Output、Tool、Sub-agent。第六个模块 Controller 是框架自己提供的推理循环；你通常是配它，比如选 LLM、skill mode、tool format，而不是自己换掉整套实现。模块还是六个，只是谁来实现，不一样。

## 别被这套推导框死

上面这个故事很好理解，但它只是默认思路，不是硬规则。实际里：

- 只有 trigger 的 creature 可以完全不要 input（`input: none`）。定时任务型 agent 没有用户也照样能跑。
- 没有 output 的 creature 也完全说得通，只做副作用就行。
- 没有 tool 的 creature 也可以存在，比如纯回复型 agent。
- 框架自己有时也会故意把抽象掰弯一点：terrarium channel 严格说更像是“一个 creature 里的 tool 写入；另一个 creature 里的 trigger 被触发”这种模式，硬要分进某个单独模块，其实不太干净。没关系。见 [boundaries](../boundaries.md)。

## 另见

- [如何组合一个 agent](composing-an-agent.md) —— 这六个模块在运行时到底怎么接起来。
- [Modules](../modules/README.md) —— 每个模块各有一篇详细说明。
- [Boundaries](../boundaries.md) —— 这个抽象什么时候适用，什么时候别太当真。