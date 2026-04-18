# skills、info 与 skill_mode 进阶

KT 的 skill 和其他框架不一样。

| | 其他框架 | KohakuTerrarium |
|---|---|---|
| 是什么 | 可调用能力单元 | 给模型看的说明文档 |
| 内容 | Python 函数 + JSON Schema | `builtin_skills/` 下的 `.md` 文件 |
| 用法 | ReAct/Planning 调用 | `info` 按需读取或框架注入 |
| 位置 | Python 模块 | `src/kohakuterrarium/builtin_skills/tools/*.md` |

skill 是工具/子智能体的使用说明书。不是能力本身。

## builtin_skills

`src/kohakuterrarium/builtin_skills/tools/` 和 `subagents/` 下的 `.md` 文件。框架自带的手册库，不是要装的 package。

## info

按名称读取完整说明的工具。不是"查帮助"——在 dynamic 模式下，它是模型补读手册的入口。

## skill_mode

控制文档怎么进 prompt。不是开关工具、不是连 MCP、不是发现 package。

```yaml
skill_mode: dynamic  # 默认：短描述进 prompt，info 补读
skill_mode: static   # 完整文档直接进系统提示词
```

dynamic：prompt短，省上下文，多一次 info 调用。
static：开局看到全部，prompt变大。

## 误解

`skill_mode` 是功能开关？不是。工具能不能用取决于 creature 暴露、MCP 连接、package 安装。skill_mode 只管文档注入。

`info` 只是查帮助？在 dynamic 下它直接影响调用质量，"先读文档再动手"的任务流靠它。

skills 等于 package？package 是分发，skills 是文档。两个概念。

## 示例

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

提示词：
```md
不确定工具参数时先调用 info。
```

改成 `skill_mode: static`，文档给法变了，工具集合没变。

## 什么时候用 static

工具不多、要开局完整说明、需要固定可审计 prompt 时。

工具多、上下文紧、按需加载时用 dynamic。

## 三层关系

MCP：能力从外部来
package：内容从安装包来
skills：把能力说明交给模型

分开"能力来源"和"文档暴露"就清楚了。

## 参考

- [英文 Configuration](../guides/configuration.md)
- [英文 Creatures](../guides/creatures.md)
- [内建工具参考](../reference/builtins.md)
- [MCP 进阶](mcp-advanced)
- [packages 进阶](packages-and-install-advanced)