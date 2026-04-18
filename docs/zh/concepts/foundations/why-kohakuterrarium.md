# KohakuTerrarium 为什么存在

## 你大概也注意过这件事

过去两年，agent 产品一下子冒出来很多：Claude Code、Codex、OpenClaw、Gemini CLI、Hermes Agent、OpenCode，等等。它们彼此确实不一样：tool 的接口不一样，controller loop 不一样，memory 策略不一样，多 agent 的思路也不一样。

但它们又都在从头重写同一层底子：

- 一个从 LLM 流式读取并解析 tool 调用的 controller
- 一个 tool 注册和分发层
- 一个给 `/loop`、后台任务、空闲检查这些场景用的 trigger system
- 一个用来隔离上下文的 sub-agent 机制
- 面向一个或多个交互面的 input / output 管线
- session、持久化、resume
- 某种形式的多 agent 连接方式

结果就是，每个团队只要想试一种新的 agent 玩法，都得先把这一套重写一遍。时间都耗在重复劳动上，真正有意思的新设计反而得往后排。

## 常见的逃法，以及它为什么行不通

最常见的反应是：“那就做一个足够通用的 agent，把所有情况都包进去。” 问题是，这条路走着走着就会撞墙：你覆盖的形态越多，特殊情况越多；特殊情况越多，这个“通用 agent”就越脆。

一年后又冒出一个新点子，这个通用 agent 装不进去，于是大家还是从头来过。

想靠一个产品把“通用性”做出来，这个方向本身就不对。

## 真正该做的事

让 **定制型 agent 变得便宜**。

如果做一种新 agent，只需要写配置、补几个自定义模块，再把这套东西怎么拼起来想明白，大家就不用一遍遍重造轮子了。那些每个 agent 都差不多要有的底层部分，集中放在一个地方就行。真正新的部分，你自己写。

KohakuTerrarium 做的就是这层底子。它是一个 **agent framework**，不是另一个 agent 产品。

## 这里说的“底子”具体指什么

先列一份具体清单，免得说虚了：

- 一套统一的事件模型。用户输入、定时器触发、tool 完成、channel 消息，外层封装都一样。
- 六模块的 creature 抽象。见 [what-is-an-agent](what-is-an-agent.md)。
- 一层 session 系统，既负责运行时持久化，也能当可搜索的知识库。
- 一层多 agent 的连接结构（terrarium）。它负责把大家接起来，自己不带 LLM。
- 原生 Python 的组合方式：每个模块都是 Python class，每个 agent 都是一个异步 Python value。
- 现成的交互入口（CLI、TUI、HTTP、WebSocket、desktop、daemon），省得你自己再写传输层。

这些正是你试新 agent 设计时最不想自己重写的东西。

## KohakuTerrarium 不是什么

- **它不是一个 agent 产品。** 你不会“运行 KohakuTerrarium”，你运行的是用它搭出来的 creature。如果你想直接试现成的 creature，可以看 [`kt-biome`](https://github.com/Kohaku-Lab/kt-biome)，它更像展示包。
- **它不是 workflow engine。** 这里没有假设你的 agent 必须按固定步骤走。
- **它不是通用 LLM wrapper。** 它也没打算往那个方向去。

## 简单说

> KohakuTerrarium 是一套造 agent 的底座。想试新东西时，不用先把底座再造一遍。

## 另见

- [什么是 agent](what-is-an-agent.md) —— 这个框架围绕的定义。
- [Boundaries](../boundaries.md) —— KT 什么时候合适，什么时候不合适。
- [kt-biome](https://github.com/Kohaku-Lab/kt-biome) —— 展示用的 creatures 和 plugin 包。