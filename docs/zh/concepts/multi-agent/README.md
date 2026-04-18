# 多智能体

KohakuTerrarium 里的多智能体有两条明确的轴线，解决的也不是一类问题。动手上 terrarium 之前，先弄清你到底要哪一种。

## 纵向（单体式）

```
      Main creature
       /   |   \
    sub   sub   sub
    (plan)(impl)(review)
```

一个主 creature 分派多个 sub-agent。每个 sub-agent 都有自己的上下文和自己的 prompt。用户看到的是一段对话，父 agent 背后藏着多段面向专项任务的对话。

Claude Code、OpenClaw、Oh-My-Opencode，以及大多数现代代码 agent，走的都是这一路子。

- **适用场景：** 任务天然可以拆成几个阶段，你也希望把上下文隔开。
- **KT 提供什么：** sub-agent 是原生能力。在 `subagents[]` 里配置，按名字调用。见 [Sub-agent](/concepts/modules/sub-agent.md)（英文）。

## 横向（模块式）

```
   +-- creature_a -------+      +-- creature_b -------+
   |     (spec agent)    | <==> |     (another spec)  |
   +---------------------+      +---------------------+
              shared channels + runtime
```

多个彼此独立的专项 creature 并排运行，各自有自己的设计。它们通过 channel 交谈。

CrewAI、AutoGen 和 MetaGPT 瞄准的是这一类。

- **适用场景：** 任务本身就是清晰的多角色流程，而且这些角色确实是不同 agent——prompt、工具、模型都不同，而不只是一个 agent 下面拆出来的几个子任务。
- **KT 提供什么：** [Terrarium](/concepts/multi-agent/terrarium.md)（英文）。Terrarium 只是接线层，不带 LLM，也不做决策。它负责运行 creatures，并管理它们之间的 channels。

## 经验判断

**先从纵向开始。** 很多人觉得“我需要多智能体”，其实更接近“我需要隔离上下文”或者“我需要一个专项 prompt”。这两件事，sub-agent 就能解决。

只有在你真的想让*不同的 creatures* 协作，而且流程已经稳定到可以画成一张拓扑图时，再去用 terrarium。

## 老实说

Terrarium 这一层还比较粗糙。现在最明显的问题是：流程能不能推进，取决于 creatures 能不能把自己的输出正确路由出去；模型一旦漏掉指令，terrarium 就可能卡住。[ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md)（英文）里写了准备怎么补，包括可配置的轮次路由、root 生命周期观察和动态管理。这块还在实验阶段。能用 sub-agent，就先用 sub-agent。

## 这一节有什么

- [Terrarium](/concepts/multi-agent/terrarium.md)（英文）——横向接线层，文档里会把它的问题说清楚。
- [Root agent](/concepts/multi-agent/root-agent.md)（英文）——位于 terrarium 外、代表用户的 creature。

## 另见

- [Sub-agent](/concepts/modules/sub-agent.md)（英文）——纵向这条路的基础单元。
- [Channel](/concepts/modules/channel.md)（英文）——terrarium 和部分 sub-agent 模式都依赖的底层机制。
