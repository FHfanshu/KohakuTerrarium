# 为什么会有 KohakuTerrarium

## 你大概已经注意到了

过去两年里，agent 产品一下子冒出来很多：Claude Code、Codex、OpenClaw、Gemini CLI、Hermes Agent、OpenCode，还有更多。

它们确实彼此不同。工具接口不同，controller loop 不同，memory 策略不同，多智能体方案也不同。

但它们又都从头重写了同一层基础设施：

- 从 LLM 流式读取并解析 tool call 的 controller
- tool registry 和 dispatch 层
- 用于 `/loop`、后台任务、空闲检查的 trigger 系统
- 用于上下文隔离的 sub-agent 机制
- 面向一个或多个交互面的输入输出管线
- session、持久化、恢复
- 某种多智能体 wiring

每个想试新 agent 形态的团队，最后都得把这些再写一遍。大量代码花在重复造基础件上，真正有意思的新设计反而要等到后面。

## 常见的逃法，为什么没用

通常的反应是：那就做一个足够通用的 agent，把各种情况都包进去。

这条路很快会撞墙。你覆盖的形态越多，特例就越多，这个通用 agent 也就越脆。一年后有人冒出新想法，发现它塞不进去，于是又从头来过。

想靠做一个单一产品来追求通用性，这个优化方向本身就不对。

## 真正该做的事

让**构建面向特定目的的 agent 变便宜**。

如果每种新 agent 形态只需要一个配置文件、少量自定义模块，再加上一套清楚的心智模型，这个领域就没必要继续重复造轮子。那层基础设施——每个 agent 都要用、而且彼此差别不大的部分——放在一个地方。真正新的部分，由你自己写。

KohakuTerrarium 做的就是这层基础设施。它是一个**构建 agent 的框架**，不是另一个 agent。

## 这里说的“substrate”是什么

具体来说，就是这些：

- 统一的事件模型。用户输入、定时器触发、tool 完成、channel 消息，都用同一种 envelope。
- 六模块的 creature 抽象。见[什么是 agent](/concepts/foundations/what-is-an-agent.md)（英文）。
- session 层，既负责运行时持久化，也是可搜索的知识库。
- 多智能体 wiring 层（terrarium），它只负责结构，本身没有 LLM。
- 原生 Python 组合：每个模块都是 Python class，每个 agent 都是一个 async Python 值。
- 开箱即用的运行时交互面（CLI、TUI、HTTP、WebSocket、desktop、daemon），这样你不用自己写 transport code。

这些东西，正是你想试一个新 agent 设计时不想再重写一遍的部分。

## KohakuTerrarium 不是什么

- **不是 agent 产品。** 你不会“运行 KohakuTerrarium”。你运行的是用它构建出来的 creature。如果你想先试一些开箱即用的 creature，可以看 [`kt-defaults`](https://github.com/Kohaku-Lab/kt-defaults)，它主要就是拿来展示这些用法的。
- **不是工作流引擎。** 这里没有假设你的 agent 一定按固定步骤走。
- **不是通用 LLM wrapper。** 它没打算做这个。

## 一句话定位

> KohakuTerrarium 是一台用来构建 agent 的机器。这样人们每次想做一种新 agent 时，就不用把这台机器再造一遍。

## 另见

- [什么是 agent](/concepts/foundations/what-is-an-agent.md)（英文）——这个框架所依据的定义。
- [边界](/concepts/boundaries.md)（英文）——什么时候 KT 合适，什么时候不合适。
- [kt-defaults](https://github.com/Kohaku-Lab/kt-defaults)——用于展示的 creature 和插件包。
