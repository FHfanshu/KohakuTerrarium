# Channel

## 它是什么

**channel** 就是一条带类型的消息管道。一头发，另一头或多头收。它可以放在某个 creature 的私有 session 里，也可以放在多个 creature 共用的 environment 里。

它不算 creature 的“核心模块”。从 chat-bot 一路讲到 agent 时，本来没有它。它更像通信底层：没有它，tool 和 trigger 在多个 agent 之间就很难接得顺。

## 为什么要有它

一旦有了 tool 和 trigger，你很快就会想让两个 agent 对话。最省事的做法是：agent A 用 tool 写一条消息；agent B 挂一个 trigger 盯着这个名字，一来消息就醒。

channel 干的就是这件事。说穿了不新鲜，就是一套命名约定，再加一点排队机制。这样“往这里写、去那边听”就能成立，双方也不必提前知道对方长什么样。

## 怎么定义它

有两种 channel：

- **`SubAgentChannel`（队列）** —— 消息按 FIFO 排队；每条消息只会被*一个*接收方消费。适合 request/response 或任务分发。
- **`AgentChannel`（广播）** —— 每个订阅者各有自己的队列；每条消息都会送到每个订阅者。适合发通知。

channel 都放在 `ChannelRegistry` 里。creature 的私有 session 有一个 registry；terrarium 的 environment 里也有一个共享 registry。creature 可以监听这两边的 channel。

`ChannelTrigger` 会把某个 channel 名接到 creature 的事件流上。只要有消息到达，就推一个 `channel_message` 事件。

## 怎么实现它

`core/channel.py` 里实现了两种 channel 类和 registry。`modules/trigger/channel.py` 里实现了把 channel 接到 creature 事件队列里的 trigger。

会自动创建的 channel 有：

- terrarium 里每个 creature 都有一个**队列**，名字就是它自己的名字，这样别的 creature 可以直接给它发私信。
- 如果有 root agent，就会多一个 `report_to_root`。

`ChannelObserver`（`terrarium/observer.py`）会给 channel 挂一个不破坏消费过程的回调：observer 能看到发出的每条消息，但不会把消息拿走。dashboard 盯队列 channel，用的就是这个办法。

## 你能拿它做什么

- **Terrarium 连线。** terrarium 配置里的每条 listen/send，最后都会落成 channel 操作。
- **群聊模式。** 任意 creature 的 `send_message` tool，加上别的 creature 上的 `ChannelTrigger`，就能拼出 N 方群聊，不用再造新原语。
- **死信 / 故障 channel。** 把错误都送到一个专门的广播 channel；再让 `logger` creature 订阅它，写盘。
- **不打断的调试。** 用 `ChannelObserver` 旁听一个队列，真正的消费者照常消费。
- **跨 creature 会合。** 两个 creature 同时监听一个共享 channel，就可以轮流处理里面的条目。

## Channels 和输出路由怎么选

Channels 并不是 creatures 之间通信的唯一方式。现在还有一个并行机制：**输出路由**。它会在每轮结束时，直接往目标 creature 的事件队列里塞一个 `creature_output` `TriggerEvent`，两边都不用自己调 `send_message`。

怎么选：

- **Channels** —— 适合条件分支（批准还是打回）、群聊、广播状态、晚点发也行/可选的消息流，以及旁听观察。是否发送、发去哪里，由 creature 自己决定。
- **输出路由** —— 适合确定性的流水线边，比如“runner 的输出永远都要交给 analyzer”。它是声明式配置，回合结束自动触发。

一个 terrarium 里完全可以两种一起用。详见 [terrarium](/zh/concepts/multi-agent/terrarium.md) 和 [terrariums 指南里的输出路由](/zh/terrariums.md#输出路由)。

## 别把它看得太死

单独跑的 creature 完全可以没有 channel。它的 tool 不发 `send_message`，trigger 也不用监听。channel 不是那条主线里的一级模块，只是框架给你准备好的一种约定。很多 multi-agent 场景转一圈，最后还是会用到它。

这也是“框架会故意掰弯自己的抽象”最明显的例子。channel 在六模块分类之外，而“agent A 告诉 agent B 一件事”却被实现成“tool 写入，trigger 触发”。层次就是故意混着来的。见 [boundaries](/zh/concepts/boundaries.md)。

## 另见

- [Tool](/zh/concepts/modules/tool.md) —— 发送这一半。
- [Trigger](/zh/concepts/modules/trigger.md) —— 接收这一半。
- [Multi-agent / terrarium](/zh/concepts/multi-agent/terrarium.md) —— channel 在这里变成实际连线。
- [Patterns](/zh/concepts/patterns.md) —— 群聊、死信、observer。