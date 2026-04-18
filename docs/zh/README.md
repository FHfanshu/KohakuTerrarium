# KohakuTerrarium 中文手册

[English](/) | **中文**

## 说明

这套文档是第三方维护的中文版本。如果内容和官方英文文档或源码不一致，以官方仓库为准：

- 官方：<https://github.com/Kohaku-Lab/KohakuTerrarium>
- 本站：<https://github.com/FHfanshu/KohakuTerrarium>

文档里提到的 `swe_bio_agent` 是本地扩展示例，不在官方仓库默认内容里。默认用的是 `@kt-defaults/creatures/swe`。

## 术语

| 英文 | 中文 | 解释 |
|------|------|------|
| creature | 智能体 | 独立运行的 agent |
| terrarium | 容器 | 多智能体环境 |
| session | 会话 | 运行记录 |
| plugin | 插件 | 扩展模块 |
| tool | 工具 | 可调用能力 |
| subagent | 子智能体 | 分派出去的智能体 |

## 文档

**先装好再往下看：**

- [安装](quickstart)
- [模型配置](llm-profiles)
- [操作方式](cli-webui)

**自己写 creature 时再看：**

- [配置写法](configuration)
- [排错](audit-and-sessions)
- [本地扩展示例](swe-bio-agent)

**进阶：**

- [MCP](mcp-advanced)
- [package 与 install](packages-and-install-advanced)
- [skills 与 skill_mode](skills-and-skill-mode-advanced)

## 示例位置

- 默认 SWE：`@kt-defaults/creatures/swe`
- 本地扩展 package：`examples/agent-apps/swe_bio_agent`
- 实际 creature：`examples/agent-apps/swe_bio_agent/creatures/swe_bio_agent`
- 强约束插件：`examples/agent-apps/swe_bio_agent/creatures/swe_bio_agent/custom/guard_plugin.py`
- 审计插件：`examples/agent-apps/swe_bio_agent/creatures/swe_bio_agent/custom/audit_plugin.py`

## 前提

装 KohakuTerrarium，装 `kt-defaults`，就能跑默认 `swe`。有本地 `swe_bio_agent` 才看扩展部分。

想深入看英文文档：
- [Concepts](/concepts/README.md)
- [Guides](/guides/README.md)
- [Reference](/reference/README.md)