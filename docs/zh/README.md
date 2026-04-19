# 琥珀生态瓶中文手册

这个项目叫 KohakuTerrarium，中文名"琥珀生态瓶"—— 一个只需改配置项，不用写代码就能搞智能体 | 多智能体协作的强劲框架

## 先跑起来

- [安装与快速开始](quickstart.md) — 装好环境、跑起第一个 creature
- [模型与预设配置](llm-profiles.md) — 怎么配模型、选模型、切模型
- [CLI 与 WebUI](cli-webui.md) — 命令行和网页界面怎么用
- [配置文件写法](configuration.md) — config.yaml 里每个字段什么意思
- [会话、审计与排错](audit-and-sessions.md) — 跑完的东西去哪了、出了问题怎么看
- [定制 SWE 智能体](swe-bio-agent.md) — 怎么在默认 swe 基础上改出你自己的版本

## 进阶专题

- [MCP 进阶](mcp-advanced.md) — MCP 服务器的高级玩法
- [kt install 与 package 进阶](packages-and-install-advanced.md) — 包管理细节
- [skills、info 与 skill_mode 进阶](skills-and-skill-mode-advanced.md) — skill 系统深挖

## 原版指南 （LLM翻译版）

- [快速上手](getting-started.md)
- [智能体](creatures.md) — creature 结构、继承、打包
- [会话](sessions.md) — 会话持久化与恢复
- [配置](configuration.md) — 按问题查配方
- [插件](plugins.md) — prompt 插件和生命周期插件
- [MCP](mcp.md) — 注册 MCP 服务器
- [包](packages.md) — kohaku.yaml、安装与发布
- [自定义模块](custom-modules.md) — 写自己的 tool/input/output/trigger/sub-agent
- [服务部署](serving.md) — kt web / kt app / kt serve
- [记忆](memory.md) — embedding、向量搜索、search_memory
- [组合](composition.md) — Python 里用 >>、&、|、* 串流程
- [容器](terrariums.md) — channel、root agent、热插拔
- [以代码方式使用](programmatic-usage.md) — 嵌入 Agent、AgentSession 等
- [前端布局](frontend-layout.md) — 面板和预设
- [示例](examples.md) — examples/ 目录下每个文件夹干什么的

## 原版教程 （LLM翻译版）

- [第一个 Creature](tutorials/first-creature.md)
- [第一个 Terrarium](tutorials/first-terrarium.md)
- [第一个 Python 嵌入](tutorials/first-python-embedding.md)
- [第一个自定义工具](tutorials/first-custom-tool.md)
- [第一个插件](tutorials/first-plugin.md)

## 不想只看用法的，往这走

- [概念](concepts/README.md) — 为什么设计成这样
- [参考](reference/README.md) — 字段、参数、签名，当字典查
- [开发](dev/README.md) — 给框架本身提 PR