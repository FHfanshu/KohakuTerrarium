# 多智能体

KohakuTerrarium 里的多智能体，分两条线，而且解决的不是同一个问题。上 terrarium 之前，先想清楚你到底需要哪一种。

## 纵向（单体式）

```
      Main creature
       /   |   \
    sub   sub   sub
    (plan)(impl)(review)
```

一个主 creature 分派多个 sub-agent。每个 sub-agent 都有自己的上下文和自己的 prompt。用户看到的是一段对话，主 agent 背后会开很多段专项对话。

Claude Code、OpenClaw、Oh-My-Opencode，还有现在大多数代码 agent，基本都是这一套。

- **什么时候用：** 任务本来就能拆成几个阶段，你又想把上下文隔开。
- **KT 给你什么：** sub-agent 是原生能力。放进 `subagents[]` 里配置，按名字调用。见 [Sub-agent](../modules/sub-agent.md)。

## 横向（模块式）

```
   +-- creature_a -------+      +-- creature_b -------+
   |     (spec agent)    | <==> |     (another spec)  |
   +---------------------+      +---------------------+
              shared channels + runtime
```

多个彼此独立的专项 creature 并排运行，各有各的设计。它们通过 channel 交流。

CrewAI、AutoGen 和 MetaGPT 做的是这一类。

- **什么时候用：** 任务本身就是明确的多角色流程，而且这些角色真的是不同 agent：prompt、工具、模型都不同，而不只是一个 agent 拆出来的几个子任务。
- **KT 给你什么：** [Terrarium](terrarium.md)。Terrarium 就是一层接线层，没有 LLM，也不做决策。它负责运行 creatures，并管理它们之间的 channels。

## 经验判断

**先用纵向。** 很多“我需要多智能体”的需求，实际是在说“我需要隔离上下文”或者“我需要一个专项 prompt”。这两件事，sub-agent 就够了。

真要上 terrarium，通常得满足两个条件：你确实要让*不同的 creatures* 协作；流程也已经稳定到能写成一张拓扑图。

## 现在的定位，实话实说

我们现在把 terrarium 看成一种**横向多智能体的候选架构**。今天已经能拼起来跑的东西包括：用 channel 处理可选/条件式消息流，用**输出路由**处理确定性的流水线边（也就是 creature 一轮结束后的文本由框架自动送进目标 creature 的事件队列，不用自己 `send_message`），再加上热插拔、观察能力，以及给 root 的生命周期信号。kt-biome 里的 `auto_research`、`deep_research`、`swe_team`、`pair_programming` 这些 terrarium，都已经在完整走这套。

我们还在继续摸索的，是“到底该怎么用起来最顺手”：什么时候该优先用输出路由、什么时候该继续用 channel；条件分支怎么表达才不用手搓一堆 channel plumbing；UI 里怎么把输出路由的活动显示得跟 channel 流量一样直观。这些开放问题都记在 [ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md) 里。

真的需要*不同 creatures* 协作时，就用 terrarium。任务如果本质上只是一个 creature 内部自然拆阶段，那还是 sub-agent 更简单。框架不会替你二选一。

## 这一节包含什么

- [Terrarium](terrarium.md) —— 横向接线层，文档里会直接说它现在有哪些问题。
- [Root agent](root-agent.md) —— 位于 terrarium 外、代表用户的 creature。

## 另见

- [Sub-agent](../modules/sub-agent.md) —— 纵向这条路的基础单元。
- [Channel](../modules/channel.md) —— terrarium 和部分 sub-agent 模式都依赖的底层机制。
