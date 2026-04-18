# Session and environment

## 它是什么

这里有两层状态：

- **session** —— 单个 creature 私有。里面放 scratchpad、私有 channel、TUI 引用、job store，以及你自定义塞进去的别的东西。
- **environment** —— 一次整体运行共享的状态，准确说是整个 terrarium 共享。里面有共享 channel registry 和一个很小的自定义 `context` dict。

单独运行的 creature 只有 session。terrarium 则有一个 environment，再给每个 creature 各配一个 session。

## 为什么要有它

multi-agent 系统里，最糟糕的默认值就是“大家什么都能共享”。如果每个 creature 都能随便改别人的 scratchpad，那你等于绕了一圈又造出一个全局可变状态。到最后根本没法调试。

这个框架的默认值正好反过来：**默认私有，共享要显式选择**。creature 先管好自己的状态；只有明确往共享 channel 里发消息时，才算真的对外。terrarium 看得到所有 creature，但 creature 只看得到自己的 session，以及自己主动监听的共享 channel。

## 怎么定义它

```
Environment（可选，每个 terrarium 一个）
├── shared_channels  (ChannelRegistry)
├── context          (dict, user-defined)
└── <这里不放私有状态>

Session（每个 creature 一个）
├── scratchpad       (key-value, private)
├── channels         (私有 ChannelRegistry；也可能别名到共享 registry)
├── tui              (TUI 引用，如果有)
├── extras           (dict, user-defined)
└── key              (session 标识)
```

规则是：

- 一个 creature 只有一个 session。
- environment 在多个 creature 之间共享；单独运行的 creature 可以不要它。
- 共享 channel 放在 environment 上。creature 只有在给某个 channel 名加了 `ChannelTrigger` 时，才算选择监听。
- scratchpad 永远是 session 私有的。

## 怎么实现它

`core/session.py` 定义了 `Session`，以及按 key 获取或创建 session 的辅助逻辑。`core/environment.py` 定义 `Environment`。`TerrariumRuntime` 会创建一个 environment，再给每个 creature 挂上一个 session。

内置 `scratchpad` tool 负责读写当前 creature 的 session scratchpad。`send_message` tool 会自己挑正确的 channel registry：先私有，找不到再去共享的。

## 你能拿它做什么

- **跨 turn 的私有记忆。** 每个 creature 都能把 scratchpad 当工作笔记本，互不串味。
- **共享会合点。** 两个 creature 同时监听一个共享 channel，就可以协作，但不用知道彼此内部怎么实现。
- **单个 creature 的状态总线。** 同一个 creature 里的几个 tool，可以把 scratchpad 当 KV 会合点用。
- **environment 级自定义上下文。** 驱动 terrarium 的 HTTP 应用，可以把 user-id、request-id 之类的信息塞进 environment 的 `context` dict，再让 plugin 去取。

## 别把它当铁律

单独运行的 creature 不一定需要 environment。纯 trigger creature 也不一定非要 scratchpad。这个框架只在真有必要的地方坚持私有 / 共享分离；如果你只有一个 creature，它也很乐意把整个状态都当成一个单独 session 来看。

## 另见

- [Channel](/zh/concepts/modules/channel.md) —— 共享是通过它显式发生的。
- [Multi-agent / terrarium](/zh/concepts/multi-agent/terrarium.md) —— environment 真正派上用场的地方。
- [impl-notes/session-persistence](/zh/concepts/impl-notes/session-persistence.md) —— session 状态在磁盘上到底怎么存。