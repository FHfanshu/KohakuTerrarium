# Prompt 聚合

## 它要解决什么问题

agent 的“system prompt”不是一整块字符串，而是几部分拼起来的：

- creature 的人格 / 角色
- 可用工具列表（名称 + 描述）
- 在这个 creature 选定的格式里，工具到底该怎么调用
- channel 拓扑信息（在 terrarium 里）
- 具名输出的说明（让 LLM 知道什么时候发到 Discord，什么时候走 stdout）
- 插件补进来的段落（项目规则、环境信息等）
- 每个工具的完整文档（`static` skill mode 下会有），或者完全不放（`dynamic` 模式下）

这些内容要是靠手写 prompt 维护，迟早会出问题：工具列表过期、调用语法写错、段落重复。框架把整件事按固定规则组装起来。

## 讨论过的做法

- **手写 prompt。** 很脆。你只要新加一个工具，就可能坏掉。
- **始终使用完整静态 prompt。** 信息全，但很大。光工具文档就可能占掉几万个 token。
- **按需加载文档。** prompt 里只放名称，让 agent 需要时再通过框架命令 `info` 拉完整文档。
- **做成可配置项。** 每个 creature 自己选取舍：`skill_mode: dynamic` 或 `skill_mode: static`。最后采用的就是这个方案。

## 实际怎么做

`prompt/aggregator.py:aggregate_system_prompt(...)` 会按下面的顺序拼接各段内容：

1. **基础 prompt。** 用 Jinja2 渲染（safe-undefined fallback），包含 creature 的人格，以及 `prompt_context_files` 里声明的项目上下文文件。
2. **工具段。**
   - `skill_mode: dynamic` → 工具*索引*：每个工具只放名称和一行描述。agent 需要完整文档时，再通过框架命令 `info` 读取。
   - `skill_mode: static` → 直接把每个工具的完整文档内联进来。
3. **Channel 拓扑段**（只用于 terrarium creature）。说明“你监听哪些 channel、能往哪些 channel 发消息、对面是谁”。这段由 `terrarium/config.py:build_channel_topology_prompt` 生成。
4. **框架提示。** 说明这个 creature 使用哪种工具调用格式（bracket / XML / native），怎么用内联框架命令（`read_job`、`info`、`jobs`、`wait`），以及输出协议是什么样。
5. **具名输出段。** 对每个 `named_outputs.<name>`，给一段简短说明，告诉模型什么时候该把文本路由到那里。
6. **Prompt 插件段。** 每个已注册的 prompt 插件都会贡献一段内容，按优先级排序（从低到高）。内置的有：`ToolListPlugin`、`FrameworkHintsPlugin`、`EnvInfoPlugin`、`ProjectInstructionsPlugin`。

接入 MCP 工具后，还会额外插入一个 “Available MCP Tools” 段，按服务器分别列出工具。

## 保持不变的约束

- **确定性。** 配置、registry 和插件集合相同，生成出的 prompt 在字节级别上保持一致。
- **自动生成的段落不会去重手写内容。** 你就算已经在 `system.md` 里写了工具列表，聚合器还是会再加一份；框架不会按内容去重。
- **Skill mode 只是一个调节项，不是策略开关。** `skill_mode` 只影响 prompt 大小这件事，系统里别的行为不会跟着变。
- **插件顺序是明确的。** 先按优先级排；优先级一样时，保持稳定的插入顺序。

## 代码里在哪

- `src/kohakuterrarium/prompt/aggregator.py` —— 负责组合 prompt 的函数。
- `src/kohakuterrarium/prompt/plugins.py` —— 内置 prompt 插件。
- `src/kohakuterrarium/prompt/templates.py` —— Jinja 的安全渲染。
- `src/kohakuterrarium/terrarium/config.py` —— channel 拓扑那一段。
- `src/kohakuterrarium/core/agent.py` —— `_init_controller()` 会在启动时调用一次聚合器。

## 另见

- [Plugin（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/modules/plugin.md) —— 怎么写 prompt 插件。
- [Tool（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/modules/tool.md) —— 工具文档怎么注册。
- [reference/configuration.md（英文）](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/reference/configuration.md) —— `skill_mode`、`tool_format`、`include_*` 这些开关。
