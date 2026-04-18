# 开发

这部分写给直接改框架的人，不是给普通用户看的。

## 提交代码前先看什么

先看顶层的 [CONTRIBUTING.md](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/CONTRIBUTING.md)，里面有环境准备、分支约定和 PR 流程。动代码前再读一遍 [CLAUDE.md](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/CLAUDE.md)。这里定了架构规则，比如 Creature、Terrarium、Root 的边界，controller 只做编排，tool 调度不能阻塞；也定了代码风格，比如现代类型标注、不要在函数里 import、用 logging 不要用 `print`。

## 这一节包括什么

- [架构](internals.md) — 16 条运行时流程的实现地图。最好配着 `src/kohakuterrarium/` 一起看。
- [测试](testing.md) — 怎么跑测试，以及怎么用 `ScriptedLLM` / `TestAgentBuilder` 这套测试工具。
- [依赖规则](dependency-graph.md) — 导入要遵守的自底向上规则，以及怎么用 `scripts/dep_graph.py` 检查。
- [前端](frontend.md) — Vue 3 仪表盘、面板注册和 WebSocket 协议。

## 什么时候该读哪篇

- 刚进项目？先看 [CONTRIBUTING.md](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/CONTRIBUTING.md)，再把 [internals.md](internals.md) 从头到尾扫一遍。
- 要加 tool、trigger 或 module？先读 [../concepts/modules/](../concepts/modules/README.md) 下面对应的概念文档。那边讲为什么，这边讲代码放哪。
- 要改 agent 生命周期或 controller 循环？先看 [internals.md §Agent runtime](internals.md#1-agent-runtime)，再看实现说明，尤其是 [non-blocking-compaction](../concepts/impl-notes/non-blocking-compaction.md) 和 [stream-parser](../concepts/impl-notes/stream-parser.md)。
- 要动持久化？先看 [session-persistence](../concepts/impl-notes/session-persistence.md)，再去看代码。

## 靠近代码的文档

`src/kohakuterrarium/` 下每个子包都有自己的 `README.md`，会说明这个目录里具体放了什么。要知道“这里到底有什么”，先看那些文件，再配合这一节一起读。