# 模式

这一页列的这些模式，都不需要框架再加新功能。
它们就是把现有模块组合起来后，自然会出现的几种用法。靠六个模块、channel、plugin，再加上 Python-native 这一层，今天就能搭出来。

你可以把这页当作一个目录来看。也可以把它当成一个证据：抽象做小一点，反而更够用。

## 1. 用 tool + trigger 做群聊

**结构。** 一个 creature 有 `send_message` tool。另一个 creature 配了 `ChannelTrigger`，监听同一个 channel 名。前者一发送，后者就会带着 `channel_message` 事件醒过来。

**为什么能行。** channel 本质上就是一个具名队列。tool 往里写，trigger 从里读。两边互相不用感知对方。

**适用场景。** 你想做横向多智能体协作，但不想把 `terrarium.yaml` 那一套搬进来；或者消息到底发不发、本轮发去哪儿，本来就是条件式决定的（比如批准还是打回、保留还是丢弃）。

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

## 1b. 用输出路由接确定性的流水线边

**结构。** 某个 creature 在自己的配置里声明 `output_wiring:`，列出一个或多个目标 creature。这样每次它一轮结束，框架都会往每个目标的事件队列里塞一个 `creature_output` `TriggerEvent` —— 里面带的是它本轮最后的 assistant 文本；如果配了 `with_content: false`，那就只发一个生命周期 ping，不带正文。

**为什么能行。** 这条线是在框架层接的：发送方不用调 tool，接收方也不用专门注册 trigger，中间也没有 channel。目标 creature 看到这个事件时，走的还是自己本来就在走的 `agent._process_event` 路径，和用户输入、timer 触发、channel 消息没什么本质不同。

**适用场景。** 这条边本来就是确定性的——“A 每做完一轮，B 都该拿到它的结果”。如果是 reviewer / navigator 这种会看内容再决定走哪条边的角色，还是更适合上一种模式（channel），因为输出路由自己不会分支。

**最小配置。**

```yaml
# terrarium.yaml 里的 creature 条目
- name: coder
  base_config: "@kt-biome/creatures/swe"
  output_wiring:
    - runner                              # 简写
    - { to: root, with_content: false }   # 生命周期 ping
```

**和 channel 的区别。** channel 要靠 LLM 记得主动发；输出路由不管 LLM 记不记得，回合结束都会自动触发。两种机制可以在同一个 terrarium 里随便混用——kt-biome 的 `auto_research` 就是用输出路由串起那些棘轮式边（ideator → coder → runner → analyzer），再用 channel 处理 analyzer 的保留/丢弃分支和团队状态广播。

## 2. 用 plugin 里的 agent 做智能守门

**结构。** 一个生命周期 plugin 挂在 `pre_tool_execute` 上。它内部会跑一个小的嵌套 `Agent`，检查这次准备执行的 tool call，然后返回 `allow` / `deny` / `rewrite`。plugin 再按结果返回改写后的参数，或者抛出 `PluginBlockError`。

**为什么能行。** plugin 是 Python，agent 也是 Python。plugin 调 agent，和调别的异步函数没本质区别。

**适用场景。** 你需要按策略拦截，但这套策略本身不简单：静态规则太死，通用方案又不贴你的业务。

## 3. 用 plugin 里的 agent 接入无感记忆

**结构。** 一个 `pre_llm_call` plugin 会先跑一个很小的检索 agent。这个检索 agent 去 session store 里找，或者去外部向量数据库里找，把和当前上下文相关的事件捞出来，汇总后作为 system message 插到前面。外层 creature 不需要主动调 tool，prompt 就已经多了上下文。

**为什么能行。** creature 不用自己判断“现在要不要检索”。plugin 每轮都会做，LLM 每轮都能看到结果。

**适用场景。** 你想要类似 RAG 的记忆能力，但不想让主 agent 为这件事花掉 tool 预算。

## 4. 用 trigger 里的 agent 做自适应监视器

**结构。** 一个自定义 trigger 的 `fire()` 里，在定时器触发时跑一个小型裁决 agent。它查看当前世界状态，然后给出 `fire / don't fire` 的判断。要是决定触发，就给外层 creature 送一个事件。

**为什么能行。** trigger 本来就是异步事件生成器。这个生成器具体看什么，由你决定；里面塞一个 mini-agent，也完全说得通。

**适用场景。** 固定轮询间隔太粗，固定规则又太脆，但你又负担得起每个 tick 跑一次完整 LLM 调用。

## 5. 静默控制器 + 外部子 agent

**结构。** 一个 creature 的 controller 不输出任何给用户看的文本，只发 tool call，最后再分派给一个子 agent。这个子 agent 配了 `output_to: external`，所以真正流到用户那边的是它的文本，父级自己不露面。

**为什么能行。** 输出路由把子 agent 的流和 controller 的流当成同级来源。你可以自己决定最后让用户看到哪一路。

**适用场景。** 你想让用户面对的是一个更专门的角色语气、格式或约束，而真正的编排器藏在幕后。`kt-biome` 里不少聊天类 creature 都是这么做的。

## 6. 把 tool 当状态总线

**结构。** 同一个 terrarium 里协作的两个 creature，把共享环境里类似 scratchpad 的 channel 当成碰头点：一个写入 `tasks_done: 3` 这样的记录，另一个去轮询。或者它们共用一个 session key，通过 `scratchpad` tool 交换状态。

**为什么能行。** session 和 environment 本来就带 KV 存储。tool 只是把这层能力露给 LLM 用。

**适用场景。** 你需要比较粗的协作，不想再专门设计一套消息传递协议。

## 7. 混合轴多智能体

**结构。** 一个 terrarium 的根层，或者其中某些 creature，内部自己也在用子 agent。顶层是横向协作；每个 creature 里面再做纵向拆分。

**为什么能行。** sub-agent 和 terrarium 是正交的，框架没拦着你一起用。

**适用场景。** 团队里已经有角色分工，而其中某些角色内部还适合继续拆开做，比如 `plan → implement → review`，但没必要把这些步骤都暴露成独立 creature。

## 8. 用框架命令做内联控制

**结构。** 在同一轮里，controller 会发出一些直接对框架说话的内联指令：`info` 按需加载某个 tool 的完整文档，`read_job` 读取后台运行中的 tool 的部分输出，`jobs` 列出待处理任务，`wait` 阻塞等待一个有状态的子 agent。这些都在当前轮里直接执行，不需要再来一次新的 LLM 往返。

语法取决于 creature 配的 `tool_format`；默认的方括号形式下，命令调用写成 `[/info]tool_name[info/]`。

**为什么能行。** framework command 是解析层给的能力，不是 tool，所以调用它们本身不占工具调用。

**适用场景。** 你想让 LLM 在一轮内部检查自己的状态，又不想为这件事占掉一个 tool slot。

## 不是封闭列表

这页重点不在这些模式本身。
重点是：模块只要够小、能组合，就会长出很多有用的结构，不需要预先硬编码进框架。这里如果有某个模式已经很接近你的需求，多半只要沿着同一套积木改一点就够了。要是你做出了新的模式，欢迎给这个文件提 PR。

## 另见

- [Agent 作为 Python 对象](/zh/concepts/python-native/agent-as-python-object.md)
  — 第 2 到第 4 种模式能成立，靠的就是这个性质。
- [Tool](/zh/concepts/modules/tool.md)、[Trigger](/zh/concepts/modules/trigger.md)、
  [Channel](/zh/concepts/modules/channel.md)、[Plugin](/zh/concepts/modules/plugin.md)
  — 这些模式就是拿这些积木拼出来的。
- [边界](/zh/concepts/boundaries.md)
  — 这些抽象只是默认做法，不是死规定；有些模式本来就会故意跨过去。
