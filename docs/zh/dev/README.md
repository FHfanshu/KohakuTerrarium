# 开发

这部分给为框架本身做贡献的人看，不是给普通用户的。

## 贡献流程

环境准备、分支约定和 PR 流程见顶层的 [CONTRIBUTING.md](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/CONTRIBUTING.md)（英文）。
动代码前先读 [CLAUDE.md](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/CLAUDE.md)（英文）。里面写了架构规则：Creature、Terrarium 和 Root 的边界，controller 作为 orchestrator，以及非阻塞 tool dispatch；也写了代码风格约定，比如使用现代类型注解、不在函数内部 import、用 logging 不用 `print`。

## 本节内容

- [架构](/dev/internals.md)（英文）— 从实现层面梳理 16 条运行时流程。建议配合 `src/kohakuterrarium/` 一起看。
- [测试](/dev/testing.md)（英文）— 如何运行测试套件，以及怎么用 `ScriptedLLM` / `TestAgentBuilder` 测试工具。
- [依赖规则](/dev/dependency-graph.md)（英文）— 叶子优先的 import 约束，以及如何用 `scripts/dep_graph.py` 检查。
- [前端](/dev/frontend.md)（英文）— Vue 3 dashboard、panel 注册和 WebSocket 协议。

## 什么时候该读什么

- 刚加入？先看 [CONTRIBUTING.md](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/CONTRIBUTING.md)（英文），再从头到尾快速过一遍 [internals.md](/dev/internals.md)（英文）。
- 要加 tool、trigger 或 module？先读 [模块相关概念文档](/concepts/modules/README.md)（英文）。概念文档讲的是为什么，这一节讲的是代码放哪。
- 要改 agent 生命周期或 controller loop？先读 [internals.md 的 Agent runtime 一节](/dev/internals.md#1-agent-runtime)（英文）和实现说明，尤其是 [non-blocking-compaction](/concepts/impl-notes/non-blocking-compaction.md)（英文）以及 [stream-parser](/concepts/impl-notes/stream-parser.md)（英文）。
- 要动持久化？先读 [session-persistence](/concepts/impl-notes/session-persistence.md)（英文），再看代码。

## 靠近代码的文档

`src/kohakuterrarium/` 下每个子包都有自己的 `README.md`，说明这个目录里有哪些文件。这些文档最接近实际情况，可以直接拿来对照代码看。