# KohakuTerrarium 中文手册

[English](/) | **中文**

第一次用 KohakuTerrarium？你来对地方了。

这组文档会手把手带你搞懂这些事：

- 装好、跑起来
- 用 CLI、WebUI、桌面端跟它交互
- 写 creature 配置文件
- 在默认 `swe` 上魔改出一个带强约束和审计留痕的本地 creature
- 查 session、审计日志、服务日志

## 先说明一件事

这套中文文档是 **第三方维护的社区版本**，不是官方文档站。

- 官方仓库：<https://github.com/Kohaku-Lab/KohakuTerrarium>
- 本站源码：<https://github.com/FHfanshu/KohakuTerrarium>
- 如果本文内容和官方英文文档、源码行为不一致，请以官方仓库最新内容为准

另外，文档里提到的 `swe_bio_agent` 是一个**本地扩展示例**，不是官方远端仓库当前默认自带的内容。

- 默认可直接使用的是 `@kt-defaults/creatures/swe`
- `swe_bio_agent` 适合当作"如何在默认 `swe` 上继续定制"的参考
- 如果你要把这套文档分发给别人，要么同时分发 `examples/agent-apps/swe_bio_agent`，要么让对方先用默认 `swe` 跑通

## 术语速查

别被英文词搞晕了，其实就这几个：

| 英文 | 中文 | 一句话解释 |
|------|------|------------|
| creature | 智能体 | 一个能独立跑的 agent |
| terrarium | 容器 | 把多个智能体编在一起的环境 |
| session | 会话 | 跑完之后留下的完整记录 |
| plugin | 插件 | 给智能体加功能的模块 |
| tool | 工具 | 智能体能调用的能力（读写文件、执行命令等） |
| subagent | 子智能体 | 被主智能体派出去干活的智能体 |

理解了这几个词，后面就顺畅了。

## 建议阅读顺序

1. [安装与快速开始](quickstart) — 先跑起来再说
2. [CLI 与 WebUI 使用](cli-webui) — 学会操作界面
3. [配置文件写法](configuration) — 搞懂配置结构
4. [定制 SWE 智能体](swe-bio-agent) — 参考本地扩展示例做一个增强版
5. [会话、审计与排错](audit-and-sessions) — 出问题怎么看
6. [模型与预设配置](llm-profiles) — 配模型、选预设

## 示例代码在哪

- 默认 SWE：`@kt-defaults/creatures/swe`
- 本地扩展示例 creature：`examples/agent-apps/swe_bio_agent`
- 强约束插件：`examples/agent-apps/swe_bio_agent/custom/guard_plugin.py`
- 审计插件：`examples/agent-apps/swe_bio_agent/custom/audit_plugin.py`

## 前提条件

- 先装 KohakuTerrarium 本体
- 再装官方默认包 `kt-defaults`
- 装完就能跑默认 `swe`
- 如果你本地也带了 `examples/agent-apps/swe_bio_agent`，再继续看增强版示例部分

## 还想深入？

中文文档覆盖入门内容。想看更多，这里有进阶：

- [Concepts](/concepts/README.md) — 核心概念和架构原理
- [Guides](/guides/README.md) — 更深入的使用指南
- [Reference](/reference/README.md) — CLI 和 API 参考