# 开发

这部分是写给会直接改框架的人看的，不是普通用户文档。

## 提交代码前先看

先读顶层的 [CONTRIBUTING.md](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/CONTRIBUTING.md)，里面有环境准备、分支约定和 PR 流程。动手前再过一遍 [CLAUDE.md](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/CLAUDE.md)。那里写了架构边界和代码风格，比如 Creature、Terrarium、Root 怎么分层，controller 只负责调度，tool 调度不能堵住主流程；也写了类型标注、import 位置、日志写法这些规矩。

## 这一节有什么

- [架构](internals.md) — 运行时流程都在这儿，最好对着 `src/kohakuterrarium/` 一起看。
- [测试](testing.md) — 怎么跑测试，`ScriptedLLM` 和 `TestAgentBuilder` 怎么用。
- [依赖规则](dependency-graph.md) — import 要怎么分层，以及怎么用 `scripts/dep_graph.py` 检查。
- [前端](frontend.md) — Vue 3 仪表盘、面板注册和 WebSocket 协议。

## 什么时候看哪篇

- 刚进项目：先看 [CONTRIBUTING.md](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/CONTRIBUTING.md)，再把 [internals.md](internals.md) 从头扫一遍。
- 要加 tool、trigger 或 module：先看 [../concepts/modules/](../concepts/modules/README.md) 里对应的概念文档。那边讲这是干嘛的，这边讲代码该放哪。
- 要改 agent 生命周期或 controller 循环：先看 [internals.md §Agent runtime](internals.md#1-agent-runtime)，再看实现说明，特别是 [non-blocking-compaction](../concepts/impl-notes/non-blocking-compaction.md) 和 [stream-parser](../concepts/impl-notes/stream-parser.md)。
- 要动持久化：先看 [session-persistence](../concepts/impl-notes/session-persistence.md)，再去读代码。

## 挨着代码的文档

`src/kohakuterrarium/` 下每个子包基本都有自己的 `README.md`，会说这个目录到底装了什么。想先摸清目录，再回来看这一节，会顺很多。
