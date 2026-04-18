# skills、`info` 和 `skill_mode` 进阶：模型到底看到了什么

这篇只讲 skills 这一层。

如果你已经知道：

- package 是通过 `kt install` 安装的分发单位
- MCP 是把外部能力接进来的协议

那接下来最容易混淆的，就是 skills。

在这个项目里，skills 更接近：

> **给模型看的工具 / 子智能体说明文档。**

---

## 先把名字理解对

这里的 skill，不要想成“训练出来的一项神秘能力”。

在 KohakuTerrarium 里，它更接近：

- tool manual
- tool docs
- sub-agent manual

也就是一份面向模型的使用说明。

这些说明会告诉模型：

- 这个工具是干什么的
- 什么时候该用，什么时候别用
- 参数怎么传
- 有哪些限制
- 常见调用方式是什么

所以 skills 这一层解决的是：

**模型怎么知道自己手里的能力该怎么用。**

---

## `builtin_skills` 是什么

框架源码里自带了一批内建说明文档，目录在：

```text
src/kohakuterrarium/builtin_skills/
  tools/
  subagents/
```

它们是框架默认的说明书来源之一。

例如内建工具和子智能体的文档，就会从这里来。

你可以把 `builtin_skills` 理解成：

- 框架自带的说明书目录
- 默认手册库

它不是让你单独去安装的 package，也不是一个需要你手动打开的独立功能模块。

---

## `info` 在这里负责什么

`info` 是一个内建工具，用来按名称读取完整说明。

它不只是“查帮助”那么简单。

在 `skill_mode: dynamic` 的情况下，`info` 实际上是模型补读完整手册的重要入口。

可以把这套关系理解成：

- prompt 里先给模型一个简短版介绍
- 模型如果需要更多细节，就调用 `info`
- `info` 再把完整文档读回来

所以 `info` 不是技能本身，而是 **读取 skill 文档的统一入口**。

---

## `skill_mode` 到底控制什么

`skill_mode` 控制的是：

> **工具说明文档如何进入模型上下文**

不是：

- 工具能不能用
- MCP 能不能连
- package 能不能被发现

现有配置里常见的是两种：

```yaml
skill_mode: dynamic
# 或
skill_mode: static
```

### `dynamic`

默认是 `dynamic`。

它的思路是：

- 先把工具的一行短描述放进 prompt
- 真要细看，再调用 `info`

优点：

- prompt 更短
- 初始上下文更省
- 工具多的时候更实用

代价：

- 可能多一次 `info` 调用
- 有时会多一个回合

### `static`

`static` 的思路是：

- 一开始就把完整工具文档直接塞进系统提示词

优点：

- 模型开局就看到全部说明
- 少一次按需读取

代价：

- prompt 会明显变大
- 工具多时上下文压力更高

---

## 最容易误会的点

### 误解 1：`skill_mode` 是功能开关

不对。

这些理解都不对：

- `skill_mode: static` 才算开启 skills
- `skill_mode: dynamic` 会关闭某些工具
- 切成 `static` 之后 MCP 才能用

都不是。

**工具是否可用**，取决于：

- creature 有没有暴露它
- MCP server 有没有连上
- package 有没有正确安装并声明

`skill_mode` 只影响文档注入方式。

### 误解 2：`info` 只是查帮助，不影响运行

也不完全对。

在动态模式下，模型往往就是靠 `info` 来补读某个工具或子智能体的完整手册。

对于要求“先读文档再动手”的任务流，这一步甚至会直接影响后续调用质量。

### 误解 3：skills 等于 package

不对。

package 是分发单位；skills 是说明文档层。

package 里可以带工具，工具可以有文档，但这不等于两者是一个概念。

---

## 一个最小示例

```yaml
name: docs-aware-agent
version: "1.0"
base_config: "@kt-defaults/creatures/swe"

skill_mode: dynamic

tools:
  - info
  - read
  - grep
```

配一个简单系统提示词：

```md
如果你不确定某个工具的参数或限制，先调用 info 读取完整说明，再继续。
```

这个例子表达的重点是：

- `read` / `grep` 是能力
- `skill_mode: dynamic` 决定文档先给短版
- `info` 负责在需要时补读完整版

如果你把它改成：

```yaml
skill_mode: static
```

变化只是：文档给模型的方式变了；不是工具集合变了。

---

## 什么时候考虑改成 `static`

默认情况下，先用 `dynamic` 就够了。

这些情况可以考虑 `static`：

- 你的工具数量不多
- 你想让模型开局就拿到完整说明
- 你更在意 prompt 的固定性和可审计性

这些情况更适合继续保留 `dynamic`：

- 工具很多
- 上下文预算紧
- 你更想把详细文档按需加载

---

## 把这一层和前两层连起来

可以这样一起看：

- **MCP**：能力从外部 server 来
- **package / `kt install`**：内容从安装包来
- **skills / `skill_mode` / `info`**：把这些能力的说明交给模型

只要把“能力来源”和“文档暴露”分开，skill 这一层就不难理解。

---

## 推荐继续读什么

- [英文 Configuration 指南](../guides/configuration.md)
- [英文 Creatures 指南](../guides/creatures.md)
- [内建工具参考](../reference/builtins.md)
- [MCP 进阶](mcp-advanced)
- [packages 与安装进阶](packages-and-install-advanced)

---

## 一句话总结

**skills 是面向模型的说明书层；`skill_mode` 决定说明是一次给全，还是靠 `info` 按需补读。**
