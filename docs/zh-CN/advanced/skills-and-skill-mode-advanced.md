# skills、info 和 skill_mode 进阶说明

先看结论：

- **工具 / 子智能体**：真正执行任务的能力
- **skill**：写给模型看的使用说明
- **info**：按名称读取某份完整说明文档
- **skill_mode**：决定说明文档是启动时直接注入，还是运行中按需读取

skill 不是工具本体。skill_mode 也不是功能开关。

---

## skill 不是什么

不是工具开关、MCP 连接、安装包、Python 函数、模型权重。

## skill 是什么

面向模型的任务说明。通常会写清楚：适合什么场景、该调哪些工具、推荐步骤、参数注意事项。

所以它解决的是：模型知不知道该怎么正确使用能力。

## 和相邻概念的区别

| 概念 | 作用 |
|---|---|
| 工具 / MCP | 提供实际能力接口 |
| 子智能体 | 作为独立角色执行某类任务 |
| skill | 提供某类任务的使用说明或 SOP |
| package | 负责安装、分发内容 |

---

## 业界里说的 skills

Claude Code、OpenCode、OpenClaw 等框架里的 skills，一般都可以理解为：**给 agent 复用的任务模块或任务说明包**。

它通常不是一句临时 prompt，而是一份结构化文档，甚至可能带有模板、脚本和依赖配置。

和普通 prompt 的区别：prompt 是一次性指令；skill 是可复用、可检索、带结构的任务说明。

和 rules 的区别：rules 更偏通用约束；skill 更偏某类任务的专门流程。当一段内容从"行为约束"变成"执行操作手册"，就该做成 skill。

和 tool / MCP 的区别：tool / MCP 提供能力，skill 说明能力怎么用。tool/MCP 是手脚，skill 是操作手册。

和 agent 的区别：agent 是完整助手角色，skill 是 agent 可按需调用的技能说明。

---

## KT 里是怎么落地的

KT 沿用了业界的思路，但做法更轻。skill 目前主要是**给模型看的 Markdown 文档**，重点不是封装独立脚本，而是补足复杂工具的使用说明。

更接近：工具说明书 / 操作手册。而不是"可执行插件包"。

### 为什么需要它

很多工具的函数签名和简短描述不足以覆盖参数细节、使用时机、推荐步骤、常见误用、失败场景的处理方式。

KT 的 skill 就是把这些内容整理成文档，供模型在需要时读取。

### 长什么样

常见位置：

- `src/kohakuterrarium/builtin_skills/tools/`
- `src/kohakuterrarium/builtin_skills/subagents/`

这里存放的是 `.md` 文档，不是插件安装包。所以 `builtin_skills` 更准确的理解是：KT 自带的模型说明书库。

### 和其他框架相比，KT 的差异

| | 其他框架 | KohakuTerrarium |
|---|---|---|
| 重点 | 任务技能包，可能带脚本和依赖 | 模型说明文档 |
| 内容形式 | `SKILL.md` + 代码 + 配置 | `builtin_skills/` 下的 `.md` |
| 作用 | 帮 agent 完成某类任务 | 帮模型正确使用工具或子智能体 |

---

## `info`：按需读取完整说明

`info` 的作用很直接：按名称读取某份完整 skill 文档。

表面上看像"查看帮助"，但在 KT 里，它通常还承担一个更实际的职责：当模型手头只有简短描述、不足以安全调用工具时，先补读完整说明。

这也是为什么 `info` 在 `dynamic` 模式下尤其重要。

什么时候应该先用 `info`？不确定参数含义、工具有前置步骤或限制、该工具比较复杂误用成本高、只看短描述不足以判断正确用法。这时先读文档，再执行工具。

---

## `skill_mode`：决定说明文档如何进入 prompt

`skill_mode` 控制的是：skill 文档以什么方式提供给模型。

它不控制：工具是否存在、MCP 是否连接成功、package 是否安装完成、某个能力是否被启用。

所以不要把它理解成"功能开关"。它只影响说明文档的注入方式。

配置示例：

```yaml
skill_mode: dynamic  # 默认：先给短描述，需要时再用 info 读取完整文档
skill_mode: static   # 启动时直接注入完整文档
```

### `dynamic`

默认模式。模型一开始通常只拿到简短描述；如果需要更多细节，再调用 `info` 读取完整文档。

优点：prompt 更短、更省上下文、工具很多时更灵活。

代价：可能多一次 `info` 调用；如果模型没先读文档，调用质量可能下降。

### `static`

完整 skill 文档在启动时就进入系统提示词。

优点：模型开局就有完整说明；不需要额外调用 `info` 才知道细节；更适合固定、可审计的提示词场景。

代价：prompt 更大；工具多时更占上下文；可能提前注入很多实际用不到的文档。

---

## 一个最常见的误区

切换 `skill_mode`，就是在切换功能是否可用？不是。

`skill_mode` 改变的是：文档开局直接给模型，还是运行中由模型通过 `info` 按需读取。

它不直接决定：`read`、`grep`、`info` 这些工具是否可用；某个 MCP 是否接入成功；某个 package 是否已经安装。

能力来源和文档暴露方式不是一回事。

---

## 一个实际配置例子

```yaml
name: docs-aware-agent
version: "1.0"
base_config: "@kt-biome/creatures/swe"

skill_mode: dynamic

tools:
  - info
  - read
  - grep
```

如果再补一条规则：

```md
不确定工具参数时先调用 info。
```

这个 agent 的执行流程就会变成：先知道有哪些工具可用，遇到不确定的工具先用 `info` 读完整说明，再调用 `read`、`grep` 等工具执行实际任务。

如果把 `skill_mode: dynamic` 改成 `skill_mode: static`，变化点主要是说明文档的提供方式变了。工具列表本身不一定变化。

---

## 该怎么选：`static` 还是 `dynamic`

更适合 `static` 的场景：工具数量不多；希望模型一开始就看到完整说明；不想依赖运行中再读文档；需要更固定、可审计的 prompt。

更适合 `dynamic` 的场景：工具很多；上下文预算紧；不想把所有说明文档都塞进 prompt；接受模型按需先调用一次 `info`。

---

## 参考

- [工具](/zh/concepts/modules/tool)
- [子智能体](/zh/concepts/modules/sub-agent)
- [MCP](//zh/guides/mcp)
- [配置](//zh/guides/configuration)
- [CLI](/zh/reference/cli)