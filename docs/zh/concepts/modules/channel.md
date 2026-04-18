# Channel

## 它是什么

**Channel** 是一条带类型的消息管道。一端发送，另一端或多端接收。Channel 可以存在于某个 creature 的私有 session 里，也可以存在于多个 creature 共享的环境里。

它不算 creature 的“规范模块”。在从 chat-bot 到 agent 的那条推导线上，它从来没出现过。它更像通信层：让工具和触发器能在 agent 之间真正连起来。

## 为什么会有它

有了工具和触发器之后，下一个需求通常就是让两个 agent 互相说话。最省事的办法是：agent A 的工具写入一条消息；agent B 配一个 trigger，监听这个名字，一有消息到达就触发。

Channel 做的就是这件事。它不是什么新发明，而是一套*命名约定*加一点排队机制，让“往这里写、在那边听”能成立，双方也不用知道彼此是谁。

## 我们怎么定义它

有两种 channel：

- **`SubAgentChannel`（队列）** — 消息按 FIFO 排队；每条消息只会被*一个*接收方消费。适合请求/响应，或者任务分发。
- **`AgentChannel`（广播）** — 每个订阅者都有自己的队列；每条消息都会送到每个订阅者。适合发通知。

Channel 都放在 `ChannelRegistry` 里。creature 的私有 session 有一个 registry；terrarium 的环境里也有一个共享 registry。creature 可以监听这两边的 channel。

`ChannelTrigger` 把 channel 名绑定到 creature 的事件流上。只要有消息到达，就会推送一个 `channel_message` 事件。

## 我们怎么实现它

`core/channel.py` 实现了两种 channel 类和 registry。`modules/trigger/channel.py` 实现了 trigger，用来把 channel 桥接到 creature 的事件队列里。

会自动创建的 channel：

- terrarium 里每个 creature 都有一个**队列**，名字就是 creature 自己的名字（这样别的 creature 可以直接给它发私信）。
- 如果存在 root agent，就会创建 `report_to_root`。

`ChannelObserver`（`terrarium/observer.py`）会给 channel 挂一个不破坏消费过程的回调：observer 能看到发出的每条消息，但不会把消息消费掉。dashboard 就是靠这个来观察那些已经有真实消费者在读取的队列 channel。

## 所以你可以做什么

- **Terrarium 连线。** terrarium 配置里的每一条 listen/send，最后都会落到 channel 操作上。
- **群聊模式。** 任意 creature 的 `send_message` 工具，加上其他 creature 上的 `ChannelTrigger`，就能组成 N 方群聊。不需要新的原语。
- **死信 / 故障 channel。** 把错误路由到一个专门的广播 channel；一个 `logger` creature 订阅它，再把内容写到磁盘。
- **非破坏式调试。** 用 `ChannelObserver` 旁听一个队列；真正的消费者照常消费，不受影响。
- **跨 creature 汇合。** 两个同时监听同一个共享 channel 的 creature，可以轮流处理里面的条目。

## 不要被它限制

单独运行的 creature 不需要 channel。它的工具不会 `send_message`，它的 trigger 也不会去监听。Channel 不是那条推导线里的一级模块；它只是框架提供的一种约定，而这个约定恰好够基础，很多多智能体场景最后都能收敛到它。

这也是“框架会主动掰弯自己的抽象”最明显的例子。Channel 放在六模块分类之外，而把“agent A 告诉 agent B 一件事”实现成“工具写入，触发器触发”，本来就是故意把层次混在一起。见[boundaries](/concepts/boundaries.md)（英文）。

## 另见

- [Tool](/concepts/modules/tool.md)（英文） — 发送这一半。
- [Trigger](/concepts/modules/trigger.md)（英文） — 接收这一半。
- [Multi-agent / terrarium](/concepts/multi-agent/terrarium.md)（英文） — channel 在这里变成实际连线。
- [Patterns](/concepts/patterns.md)（英文） — 群聊、死信、observer。
