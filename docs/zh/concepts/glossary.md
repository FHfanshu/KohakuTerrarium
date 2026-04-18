# 术语表

这里用通俗的话解释 KohakuTerrarium 里的常用词。你如果在某篇文档里读到一半，被某个词绊住了，就来这里查。每一项都链接到更完整的概念文档。

## Creature

一个自包含的 agent。这是 KohakuTerrarium 里的一级抽象。一个 creature 有 controller、tools、triggers、（通常还有）sub-agents、input、output、session，以及可选的 plugins。它可以单独运行，也可以放进 terrarium 里运行。详见：[什么是 agent](/concepts/foundations/what-is-an-agent.md)（英文）。

## Controller

creature 里的推理循环。它从队列里取事件，请 LLM 响应，分发返回的 tool 调用和 sub-agent 调用，把结果作为新事件再喂回去，并决定要不要继续循环。它不是“大脑”——LLM 才是；controller 是让 LLM 能持续运作的那层循环。详见：[controller](/concepts/modules/controller.md)（英文）。

## Input

外部世界把用户消息交给 creature 的方式。实际上一共就是某一种 trigger：标记为 `user_input` 的那种。内置实现包括 CLI、TUI、Whisper ASR 和 `none`（只靠 trigger 唤醒的 creatures）。详见：[input](/concepts/modules/input.md)（英文）。

## Trigger

任何不靠显式用户输入、但会唤醒 controller 的东西。定时器、空闲检测器、webhook、频道监听器、监控条件都算。每个 trigger 都会把 `TriggerEvent` 推进 creature 的事件队列。详见：[trigger](/concepts/modules/trigger.md)（英文）。

## Output

creature 向外部世界回话的方式。router 会接住 controller 发出的所有内容（文本分块、tool 活动、token 用量），再分发到一个或多个 sink，比如 stdout、TTS、Discord 或文件。详见：[output](/concepts/modules/output.md)（英文）。

## Tool

LLM 可以带参数调用的一项能力。比如 shell 命令、文件编辑、网页搜索。tool 也可以是消息总线、状态句柄，或者嵌套 agent。框架不管你背后具体怎么做。详见：[tool](/concepts/modules/tool.md)（英文）。

## Sub-agent

父级为了处理一件边界明确的事，临时拉起来的嵌套 creature。它有自己的上下文，通常也只拿到父级 tools 里的一部分。站在 LLM 的视角，调用 sub-agent 和调用普通 tool 没太大区别。详见：[sub-agent](/concepts/modules/sub-agent.md)（英文）。

## TriggerEvent

所有外部信号统一进入系统时用的那层封装。用户输入、定时器触发、tool 完成、频道消息、sub-agent 输出，最后都会变成 `TriggerEvent(type=..., content=..., ...)`。入口只有一种，代码路径也只有一条。详见：[组合 agent](/concepts/foundations/composing-an-agent.md)（英文）。

## Channel

一条具名消息管道。分两种：**queue**（每条消息只给一个消费者，FIFO）和 **broadcast**（每个订阅者都会收到每条消息）。channel 要么放在 creature 的私有 session 里，要么放在 terrarium 的共享 environment 里。跨 creature 通信靠的是 `send_message` tool 加上 `ChannelTrigger`。详见：[channel](/concepts/modules/channel.md)（英文）。

## Session

每个 creature 的**私有**状态：scratchpad、私有 channels、TUI 引用、运行中 jobs 的存储。会序列化到 `.kohakutr` 文件。每个 creature 实例对应一个 session。详见：[session and environment](/concepts/modules/session-and-environment.md)（英文）。

## Environment

terrarium 内跨 creature **共享**的状态：共享 channel 注册表，以及可选的共享上下文字典。creature 默认是私有的，只有显式选择后才会共享——它只会看到自己明确监听的共享 channels。详见：[session and environment](/concepts/modules/session-and-environment.md)（英文）。

## Scratchpad

creature 的 session 里有一个键值存储。它会跨多个 turn 保留，可以通过 `scratchpad` tool 读写。适合当工作记忆，也适合让协作中的 tools 在这里碰头。

## Plugin

plugin 改的是*模块之间的连接方式*，不是去 fork 某个模块。分两类：**prompt plugins**（往 system prompt 里补内容）和 **lifecycle plugins**（挂到 `pre_llm_call`、`post_tool_execute` 之类的钩子上）。`pre_*` hook 可以抛出 `PluginBlockError` 来中止一次操作。详见：[plugin](/concepts/modules/plugin.md)（英文）。

## Skill mode

一个配置项（`skill_mode: dynamic | static`），决定 system prompt 是一开始就带上完整 tool 文档（`static`，更大），还是只带名称和一句简介，等 agent 需要时再通过 `info` 框架命令展开（`dynamic`，更小）。这只是取舍，别的行为不变。详见：[prompt aggregation](/concepts/impl-notes/prompt-aggregation.md)（英文）。

## Framework commands

这是 LLM 在一个 turn 进行到一半时可以发出的内联指令，用来直接和框架交互，不必走完整的 tool 往返。它们和 **tool 调用用的是同一套语法族**——取决于 creature 配置的 `tool_format`，可能是 bracket、XML 或 native。这里叫“command”，说的是*意图*（和框架对话，而不是运行某个 tool），不是说它有另一套语法。

在默认的 bracket 格式里：

- `[/info]tool_or_subagent_name[info/]` —— 按需加载某个 tool 或 sub-agent 的完整文档。
- `[/read_job]job_id[read_job/]` —— 读取一个运行中或已完成后台 job 的输出（正文里支持 `--lines N` 和 `--offset M` 参数）。
- `[/jobs][jobs/]` —— 列出当前正在运行的后台 jobs（含它们的 ID）。
- `[/wait]job_id[wait/]` —— 阻塞当前 turn，直到某个后台 job 完成。

command 名和 tool 名共用一个命名空间；“读取 job 输出”这个命令特意叫 `read_job`，就是为了不和读文件的 `read` tool 撞名。

## Terrarium

一个专门负责把多个 creatures 接起来一起跑的层。它没有 LLM，也不做决策，就是一个运行时加一组共享 channels。creatures 不需要知道自己是不是在 terrarium 里；单独跑也照样成立。这部分现在还有些边角没磨平，可以看 [roadmap](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md)（英文）。详见：[terrarium](/concepts/multi-agent/terrarium.md)（英文）。

## Root agent

位于 terrarium *外部*、但在其中代表用户的 creature。从结构上看，它就是一个普通 creature；之所以叫“root”，是因为它会自动拿到 terrarium 管理工具集，也因为它是用户在系统里的对口方。详见：[root agent](/concepts/multi-agent/root-agent.md)（英文）。

## Package

一个可安装目录，里面可以放 creatures、terrariums、自定义 tools、plugins、LLM 预设和 Python 依赖，并由 `kohaku.yaml` 清单描述。通过 `kt install` 安装到 `~/.kohakuterrarium/packages/` 下。在配置和 CLI 里用 `@<pkg>/<path>` 语法引用。详见：[packages guide](/guides/packages.md)（英文）。

## kt-defaults

官方提供的开箱即用包，里面有一批实用的 creatures、terrariums 和 plugins，以 package 的形式发布。它不属于核心框架，更像展示样例和起步材料。见 [github.com/Kohaku-Lab/kt-defaults](https://github.com/Kohaku-Lab/kt-defaults)（英文）。

## Compose algebra

一小组操作符：`>>` 顺序、`&` 并行、`|` 回退、`*N` 重试、`.iterate` 异步循环，用来在 Python 里把 agents 串成流水线。它本质上是语法糖，建立在“agent 是一等异步 Python 值”这个事实之上。详见：[composition algebra](/concepts/python-native/composition-algebra.md)（英文）。

## MCP

Model Context Protocol，一种把 tools 暴露给 LLM 的外部协议。KohakuTerrarium 可以通过 stdio 或 HTTP/SSE 连接 MCP server，发现其中的 tools，再通过元工具（`mcp_call`、`mcp_list` 等）把它们暴露给 LLM。详见：[mcp guide](/guides/mcp.md)（英文）。

## Compaction

当上下文快装满时，后台会把较早的对话 turn 总结掉。这个过程不阻塞：controller 会继续运行，summariser 在后台工作，真正替换上下文发生在 turn 与 turn 之间，而且是原子完成的。详见：[non-blocking compaction](/concepts/impl-notes/non-blocking-compaction.md)（英文）。

## 另见

- [概念索引](/concepts/README.md)（英文）——看整个 concepts 目录。
- [什么是 agent](/concepts/foundations/what-is-an-agent.md)（英文）——更完整的背景，很多词会一起在那篇里出现。
- [边界](/concepts/boundaries.md)（英文）——什么时候该把上面这些东西视为可选项。
