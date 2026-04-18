# Session 与 environment

## 它是什么

这里有两层状态：

- **Session** —— 只属于一个 creature。里面放这个 creature 的 scratchpad、私有 channel、TUI 引用、job store，以及其他自定义内容。
- **Environment** —— 整个运行过程共享；更准确地说，是整个 terrarium 共享。里面放共享 channel registry，还有一个很小的自定义上下文字典。

单独运行的 creature 只有 session。terrarium 则有一个 environment，并且每个 creature 各有一个 session。

## 为什么会有它

在多智能体系统里，最糟糕的默认值就是“所有东西都共享”。如果每个 creature 都能改别人的 scratchpad，那你其实是在绕一圈实现全局可变状态，调试基本没法做。

这个框架反过来：**默认私有，共享要显式加入**。creature 默认只保留自己的状态；只有明确发到共享 channel，别人才看得到。能看到所有 creature 的只有 terrarium。creature 自己只能看到自己的 session，以及它主动选择监听的共享 channel。

## 我们怎么定义它

```
Environment（可选，每个 terrarium 一个）
├── shared_channels  (ChannelRegistry)
├── context          (dict，用户自定义)
└── <这里没有私有状态>

Session（每个 creature 一个）
├── scratchpad       (键值存储，私有)
├── channels         (私有 ChannelRegistry；也可以别名到共享 channel)
├── tui              (TUI 引用，适用时存在)
├── extras           (dict，用户自定义)
└── key              (session 标识符)
```

规则：

- 一个 creature 只会有一个 session。
- environment 在多个 creature 之间共享。单独运行的 creature 可以没有它。
- 共享 channel 放在 environment 上。creature 要加入某个共享 channel，需要为该 channel 名添加一个 `ChannelTrigger`。
- scratchpad 始终是 session 私有的。

## 我们怎么实现它

`core/session.py` 定义了 `Session`，以及按 key 获取或创建 session 的辅助函数。`core/environment.py` 定义了 `Environment`。`TerrariumRuntime` 会创建一个 environment，再给每个 creature 绑定一个 session。

内置工具 `scratchpad` 读写的是当前 creature 的 session scratchpad。`send_message` 工具会选择合适的 channel registry：先查私有的，再查共享的。

## 所以你可以做什么

- **跨轮次的私有记忆。** 每个 creature 都可以把 scratchpad 当作自己的工作笔记本，用完也不会泄露出去。
- **共享汇合点。** 两个 creature 只要都在监听同一个共享 channel，就能配合工作，不需要知道彼此内部怎么实现。
- **把 session 当成单个 creature 的状态总线。** 同一个 creature 里的协作工具，可以把 scratchpad 当作 KV 汇合点。
- **挂在 environment 上的自定义上下文。** 驱动 terrarium 的 HTTP 应用可以把 user identity、request id 之类的信息放进 environment 的 `context` 字典，让插件去读取。

## 别被它框住

单独运行的 creature 不一定需要 environment。只有 trigger 的 creature 也不一定非要 scratchpad。框架只在该区分私有和共享的地方强制区分；如果只有一个 creature，它也完全可以只把 session 当成全部状态。

## 另见

- [Channel](/concepts/modules/channel.md)（英文）—— 显式加入的共享原语。
- [Multi-agent / terrarium](/concepts/multi-agent/terrarium.md)（英文）—— environment 在这里才真正起作用。
- [impl-notes/session-persistence](/concepts/impl-notes/session-persistence.md)（英文）—— session 状态在磁盘上到底怎么存。
