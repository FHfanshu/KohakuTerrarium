# 什么是 agent

在 KohakuTerrarium 里，agent 就是 **creature**。想看懂 creature 为什么长这样，最直接的办法是从零一点点搭出来。

## 第 0 阶段 — 聊天机器人

```
    +-------+      +-----+      +--------+
    | Input | ---> | LLM | ---> | Output |
    +-------+      +-----+      +--------+
```

用户输入，模型回答，答案被打印出来。这已经是对话式 AI 最简单的形态了。它能*说话*，但不能*做事*。

## 第 1 阶段 — 加上工具系统

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

给 LLM 加上调用工具的能力：shell 命令、文件编辑、网页搜索。现在它可以行动了。它不再只是聊天机器人，而是 smolagent 或 swe-agent 那个意义上的 agent。

这已经很有用了，但限制也马上出现：想让这个 agent 做事，唯一的办法还是*给它打字*。

## 第 2 阶段 — 加上触发系统

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

真正的 agent 不能总等用户输入才醒过来。比如 `/loop` 功能、后台任务结束、空闲检查、webhook、定时器。总得有个东西盯着外部世界，在条件满足时触发 controller。这个东西就是 **trigger**。

有了 trigger 之后，你很快会发现：*用户输入本身也只是 trigger 的一种*。所以“input”其实成了更一般的唤醒机制里的一个特例。Claude Code 和 OpenClaw 大致就在这一层。

## 第 3 阶段 — 加上 sub-agent

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

上下文窗口是有限的。一个长任务如果带着很多探索性的子步骤，而每一步都落进父级对话里，很快就会把上下文预算吃光。

解决办法是生成一个 **sub-agent**：它是嵌套的 creature，用自己的上下文运行，最后回传压缩后的结果，然后消失。还有一点很重要：从父级视角看，sub-agent *本质上也只是一个工具*——调用它，它返回结果。现在的现代编码 agent 基本都走到这一步了。

## 六模块 creature

合起来看：

| 模块 | 作用 |
|---|---|
| **Controller** | 推理循环。它从 LLM 流式接收输出，解析工具调用，再分发执行。 |
| **Input** | 告诉 controller 要做什么（一种特定的 trigger）。 |
| **Trigger** | 外部世界需要它行动时，负责触发 controller。 |
| **Tool** | agent 用来做事的东西。 |
| **Sub-agent** | 嵌套的 creature；在概念上也算一种工具。 |
| **Output** | agent 如何向它所处的世界回话。 |

**creature** 就是这六个模块放在一起。它是 KohakuTerrarium 里的一级抽象，所有指南、参考文档和其他概念文档，最后讲的都是它。

这里先说明一个容易混淆的点：如果你在根 README 或指南里看到“可以扩展的五种模块类型”，说的是五个可以由用户替换的模块——Input、Trigger、Output、Tool、Sub-agent。第六个模块 Controller 是框架提供的推理循环；你会配置它，比如 LLM、skill mode、tool format，而不是去替换它的实现。还是六个模块，只是实现方不一样。

## 别被这套推导绑住

上面的推导适合作为默认理解，不是硬规则。实际里：

- 只有 trigger 的 creature 可以完全跳过 input（`input: none`）。定时任务 agent 没有用户照样能跑。
- 没有 output 的 creature 也是成立的（只产生副作用）。
- 没有 tool 的 creature 也可以存在（纯响应式 agent）。
- 框架自己在方便时也会稍微掰弯这套抽象：terrarium channel 从技术上说更像“一个 creature 里的 tool 写入，另一个 creature 里的 trigger 被触发”这种模式，干净地塞进任何一个模块都不太合适。没关系。见[边界](/concepts/boundaries.md)（英文）。

## 另见

- [组合 agent](/concepts/foundations/composing-an-agent.md)（英文）—— 六个模块在运行时到底怎么接起来。
- [模块](/concepts/modules/README.md)（英文）—— 每个模块各一篇，展开讲。
- [边界](/concepts/boundaries.md)（英文）—— 这套抽象是默认值，不是定律。
