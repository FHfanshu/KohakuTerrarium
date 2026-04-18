# Prompt 聚合

## 这个问题是什么

agent 的“system prompt”并不是一整块字符串，而是几部分拼起来的：

- creature 的人格 / 角色
- 可用工具列表（名称 + 描述）
- 这个 creature 选定的工具调用格式
- channel 拓扑信息（在 terrarium 里）
- 具名输出的说明（让 LLM 知道什么时候发到 Discord，什么时候走 stdout）
- 插件补进来的段落（项目规则、环境信息等）
- 每个工具的完整文档（`static` skill mode 下会带上），或者完全不带（`dynamic` 模式下）

这些内容如果靠手写 prompt 维护，很容易出问题：工具列表过期、调用语法写错、段落重复。框架把这件事按固定规则组装起来。

## 考虑过的方案

- **手写 prompt。** 很脆。你只要加一个工具，就可能出错。
- **始终用完整静态 prompt。** 信息是全的，但体积很大。光工具文档就可能有几万个 token。
- **按需加载文档。** prompt 里只放名称，agent 需要时再通过框架命令 `info` 去拉完整文档。
- **做成可配置项。** 每个 creature 自己选取舍：`skill_mode: dynamic` 或 `skill_mode: static`。最后用的是这个方案。

## 实际怎么做

`prompt/aggregator.py:aggregate_system_prompt(...)` 会按下面的顺序把各段内容拼起来：

1. **基础 prompt。** 用 Jinja2 渲染（safe-undefined fallback），包含 creature 的人格，以及 `prompt_context_files` 里声明的项目上下文文件。
2. **工具段。**
   - `skill_mode: dynamic` → 工具*索引*：每个工具只放名称和一行描述。agent 需要完整文档时，再通过框架命令 `info` 读取。
   - `skill_mode: static` → 直接把每个工具的完整文档内联进来。
3. **Channel 拓扑段**（只用于 terrarium creature）。说明“你监听哪些 channel、能往哪些 channel 发消息、对面是谁”。这段由 `terrarium/config.py:build_channel_topology_prompt` 生成。
4. **框架提示。** 说明这个 creature 用哪种工具调用格式（bracket / XML / native），怎么用内联框架命令（`read_job`、`info`、`jobs`、`wait`），以及输出协议长什么样。
5. **具名输出段。** 对每个 `named_outputs.<name>`，给一小段说明，告诉模型什么时候该把文本路由到那里。
6. **Prompt 插件段。** 每个已注册的 prompt 插件都会贡献一段内容，按优先级排序（从低到高）。内置的有：`ToolListPlugin`、`FrameworkHintsPlugin`、`EnvInfoPlugin`、`ProjectInstructionsPlugin`。

接入 MCP 工具后，还会额外插入一个“Available MCP Tools”段，按服务器分别列出工具。

## 保住了哪些不变量

- **确定性。** 配置、registry 和插件集合一样，生成出的 prompt 就会在字节级别保持一致。
- **自动生成的段落不会和手写内容去重。** 就算你已经在 `system.md` 里写了工具列表，聚合器还是会再加一份；框架不会按内容去重。
- **Skill mode 只是调节项，不是策略开关。** `skill_mode` 只影响 prompt 大小，不会改系统里其他行为。
- **插件顺序是明确的。** 先按优先级排；优先级相同时，保持稳定的插入顺序。

## 代码在哪

- `src/kohakuterrarium/prompt/aggregator.py` —— 负责组合 prompt 的函数。
- `src/kohakuterrarium/prompt/plugins.py` —— 内置 prompt 插件。
- `src/kohakuterrarium/prompt/templates.py` —— Jinja 的安全渲染。
- `src/kohakuterrarium/terrarium/config.py` —— channel 拓扑那一段。
- `src/kohakuterrarium/core/agent.py` —— `_init_controller()` 会在启动时调用一次聚合器。

## 另见

- [Plugin](../modules/plugin.md) —— 怎么写 prompt 插件。
- [Tool](../modules/tool.md) —— 工具文档怎么注册。
- [reference/configuration.md — `skill_mode`, `tool_format`, `include_*`](../../reference/configuration.md) —— 相关开关。
