# KohakuTerrarium 中文手册

[English](/) | **中文**

第一次用 KohakuTerrarium？可以先从这里开始。

这组文档主要帮你解决这些事：

- 完成安装并跑通第一个示例
- 用 CLI、WebUI 和桌面端交互
- 编写 creature 配置文件
- 基于默认 `swe` 做一个带强约束和审计留痕的本地 creature
- 查看 session、审计日志和服务日志

## 先说明一件事

这套中文文档是 **第三方维护的社区版本**，不是官方文档站。

- 官方仓库：<https://github.com/Kohaku-Lab/KohakuTerrarium>
- 本站源码：<https://github.com/FHfanshu/KohakuTerrarium>
- 如果本文内容和官方英文文档、源码行为不一致，请以官方仓库最新内容为准

另外，文档里提到的 `swe_bio_agent` 是一个**本地扩展示例**，不是官方远端仓库当前默认自带的内容。

- 默认可直接使用的是 `@kt-defaults/creatures/swe`
- `swe_bio_agent` 更适合作为“如何继续定制默认 `swe`”的参考
- 如果你要把这套文档分发给别人，要么同时提供 `examples/agent-apps/swe_bio_agent`，要么先让对方用默认 `swe` 跑通

## 术语速查

先记住这几个常见词：

| 英文 | 中文 | 一句话解释 |
|------|------|------------|
| creature | 智能体 | 一个可以独立运行的 agent |
| terrarium | 容器 | 把多个智能体组织在一起的环境 |
| session | 会话 | 一次运行留下的完整记录 |
| plugin | 插件 | 给智能体扩展能力的模块 |
| tool | 工具 | 智能体可以调用的能力（读写文件、执行命令等） |
| subagent | 子智能体 | 被主智能体分派出去处理任务的智能体 |

把这几个词对上，后面的内容就更容易读了。

## 先看这几篇（最简单但必要）

1. [安装与快速开始](quickstart) — 先把环境装好并跑通
2. [模型与预设配置](llm-profiles) — 把模型和默认配置先弄对
3. [CLI 与 WebUI 使用](cli-webui) — 了解最常用的操作方式

## 用到再看

1. [配置文件写法](configuration) — 开始自己写 creature 时再看
2. [会话、审计与排错](audit-and-sessions) — 需要查 session、日志、排错时再看
3. [定制 SWE 智能体](swe-bio-agent) — 想基于本地扩展示例做增强版时再看

## 进阶专题

1. [MCP 进阶](mcp-advanced) — 理清 MCP 是什么、怎么接进 creature
2. [`kt install` 与 package 进阶](packages-and-install-advanced) — 理清 package、安装方式和 `@pkg/path`
3. [skills、`info` 与 `skill_mode` 进阶](skills-and-skill-mode-advanced) — 理清模型看到的说明文档是怎么来的

## 前提条件

- 先装 KohakuTerrarium 本体
- 再装官方默认包 `kt-defaults`
- 装完后就可以直接跑默认 `swe`
- 如果你本地也有 `examples/agent-apps/swe_bio_agent`，再继续看增强版示例部分

## 示例代码在哪

- 默认 SWE：`@kt-defaults/creatures/swe`
- 本地扩展示例 creature：`examples/agent-apps/swe_bio_agent`
- 强约束插件：`examples/agent-apps/swe_bio_agent/custom/guard_plugin.py`
- 审计插件：`examples/agent-apps/swe_bio_agent/custom/audit_plugin.py`

## 还想深入？

中文文档主要覆盖入门内容。想继续深入，可以看这些：

- [Concepts](/concepts/README.md) — 核心概念和架构原理
- [Guides](/guides/README.md) — 更深入的使用指南
- [Reference](/reference/README.md) — CLI 和 API 参考