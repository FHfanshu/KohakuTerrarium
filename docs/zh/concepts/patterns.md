# 模式

这一页里的模式，都不需要框架新增功能。
它们只是把现有模块拼在一起后的常见做法。六个模块、channel、plugin，再加上 Python-native 这一层，今天就能搭出这些结构。

你可以把这页当清单看，也可以把它当成一个侧面证明：抽象做小，确实有用。

## 1. 用 tool + trigger 做群聊

**结构。** 一个 creature 带有 `send_message` tool。另一个 creature 配置了 `ChannelTrigger`，监听同一个 channel 名。前者发消息后，后者会收到 `channel_message` 事件并被唤醒。

**为什么可行。** channel 只是一个具名队列。tool 往里写，trigger 从里读。两边彼此不用知道对方的存在。

**适用场景。** 你想做横向多智能体协作，但不想引入 `terrarium.yaml` 那套机制。

**最小配置。**

```yaml
# creature_a
tools:
  - name: send_message

# creature_b
triggers:
  - type: channel
    options:
      channel: chat
```

## 2. 用 plugin 里的 agent 做智能守卫

**结构。** 一个生命周期 plugin 挂在 `pre_tool_execute`。它的实现里会运行一个小型嵌套 `Agent`，检查即将执行的 tool call，然后返回 `allow` / `deny` / `rewrite`。plugin 再据此返回改写后的参数，或者抛出 `PluginBlockError`。

**为什么可行。** plugin 是 Python，agent 也是 Python。plugin 调 agent，和调别的异步函数没区别。

**适用场景。** 你需要按策略做拦截，但这套策略本身并不简单：静态规则不够用，通用方案又不贴合你的领域。

## 3. 用 plugin 里的 agent 接入无感记忆

**结构。** 一个 `pre_llm_call` plugin 会先跑一个很小的检索 agent。这个检索 agent 会去 session store（或者外部向量数据库）里找和当前上下文相关的事件，汇总命中结果，然后把它们作为 system message 插到前面。外层 creature 不需要显式调用 tool，prompt 就会自动带上更多上下文。

**为什么可行。** creature 不用自己判断“现在要不要检索”——plugin 每轮都会做，LLM 每轮都能看到结果。

**适用场景。** 你想要类似 RAG 的记忆能力，但不想让主 agent 为此消耗 tool 预算。

## 4. 用 trigger 里的 agent 做自适应监视器

**结构。** 一个自定义 trigger 的 `fire()` 方法里，在定时器触发时运行一个小型裁决 agent。这个 agent 会查看当前世界状态，然后给出 `fire / don't fire` 的决定。若决定触发，就向外层 creature 发送一个事件。

**为什么可行。** trigger 本质上只是异步事件生成器。生成器具体看什么，由你决定；“内嵌一个 mini-agent”也完全说得通。

**适用场景。** 固定轮询间隔太粗，固定规则又太脆，但你又能接受每个 tick 跑一次完整 LLM 调用的成本。

## 5. 静默控制器 + 外部子 agent

**结构。** 一个 creature 的 controller 不输出面向用户的文本——只发 tool call，最后再分派给一个子 agent。这个子 agent 配了 `output_to: external`，所以真正流给用户的是*它*的文本，父级保持不可见。

**为什么可行。** 输出路由会把子 agent 的流当成和 controller 同级的输出来源。你可以决定最终让用户看到哪一路。

**适用场景。** 你希望用户面对的是某个专门角色的说话方式、格式或约束，而编排器藏在幕后。`kt-defaults` 里不少聊天类 creature 都是这么做的。

## 6. 把 tool 当状态总线

**结构。** 在同一个 terrarium 里协作的两个 creature，把共享环境里类似 scratchpad 的 channel 当作碰头点：一个写入 `tasks_done: 3` 这样的记录，另一个轮询读取。或者，它们通过共享的 session key 使用 `scratchpad` tool。

**为什么可行。** session 和 environment 本来就有 KV 存储。tool 只是把这层能力暴露给 LLM。

**适用场景。** 你需要比较粗粒度的协作，但不想专门设计一套消息传递协议。

## 7. 混合轴多智能体

**结构。** 一个 terrarium 的根层级（或者其中的 creature）内部自己也在用子 agent。顶层是横向协作；每个 creature 内部再做纵向拆分。

**为什么可行。** sub-agent 和 terrarium 是正交的。框架没有限制你把两者一起用。

**适用场景。** 团队里已经有明确分工，而其中某些角色内部还适合继续拆分（plan → implement → review），但没必要把这些步骤都暴露成独立 creature。

## 8. 用框架命令做内联控制

**结构。** 在同一轮里，controller 会发出一些直接对框架说话的内联指令：`info` 按需加载某个 tool 的完整文档，`read_job` 读取后台运行中 tool 的部分输出，`jobs` 列出待处理工作，`wait` 等待一个有状态的子 agent。这些都在当前轮内执行，不需要再走一次新的 LLM 往返。

语法取决于 creature 配置的 `tool_format`；默认的方括号形式下，命令调用写成 `[/info]tool_name[info/]`。

**为什么可行。** framework command 是解析层提供的能力，不是 tool。调用它们本身不花成本。

**适用场景。** 你想让 LLM 在同一轮中检查自己的状态，但又不想为此占掉一个 tool slot。

## 不是封闭列表

这页的重点，不是这些模式本身。
重点在于：小而可组合的模块，会自然长出很多有用的结构，你不需要把它们硬编码进框架。如果这里某个模式和你的需求很接近，通常只要在同一组积木上稍微改一下就够了。要是你做出了新的模式，欢迎给这个文件提 PR。

## 另请参阅

- [Agent 作为 Python 对象](/concepts/python-native/agent-as-python-object.md)（英文）
  — 让第 2 到第 4 种模式成立的前提。
- [Tool](/concepts/modules/tool.md)（英文）、[Trigger](/concepts/modules/trigger.md)（英文）、
  [Channel](/concepts/modules/channel.md)（英文）、[Plugin](/concepts/modules/plugin.md)（英文）——这些模式就是拿它们拼出来的。
- [边界](/concepts/boundaries.md)（英文）——抽象是默认做法，不是铁律；有些模式会有意越过这条默认边界。
