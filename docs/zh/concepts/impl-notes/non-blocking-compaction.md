# 非阻塞压缩

## 要解决的问题

一个连续运行数小时的 creature，会不断积累对话。时间一长，提示词就会超出模型的上下文预算。常见做法是压缩：把旧轮次总结成一段简短说明，最近几轮保留原样。

问题是，压缩本身也要发起一次 LLM 调用。如果控制器得等总结器跑完，环境型 agent 就会卡住几十秒，眼看着 50k token 被重写。

对代码代理那类 creature，这还勉强能接受。对监控型或对话型 creature，这就是产品问题了。

## 考虑过的方案

- **同步暂停。** 停下控制器，做完总结，再继续。实现简单，但卡顿时间很长。
- **交给另一个 agent。** 这件事本质上只是“把旧轮次改写成一段话”，单独起一个 agent 太重了。
- **后台任务 + 原子替换。** 一边让控制器继续跑，一边并行做总结；等到轮次之间再把对话替换掉。框架现在用的就是这个办法。

## 实际做法

概念上，对话会分成两个区：

```
  [ ----- 压缩区 ----- ][ --- 活跃区（keep_recent_turns）--- ]
           可压缩                           原样保留，永不总结
```

流程如下：

1. 每轮结束后，compact manager 会检查
   `prompt_tokens >= threshold * max_tokens`。
2. 如果满足条件，就发出一个 `compact_start` 活动事件，并启动一个后台 `asyncio.Task`。
3. 这个任务会：
   - 对压缩区做快照；
   - 调用总结用的 LLM（默认用主控制器的 LLM；如果配置了更便宜的 `compact_model`，就用它）；
   - 生成摘要，并把决策、文件路径、错误字符串等高信号 token 原样保留下来。
4. 这时控制器不会停。工具照常运行，sub-agent 可以继续启动，用户也可以继续输入。
5. 摘要准备好以后，manager 会等当前轮次结束，再**原子地**改写对话：
   - 旧的压缩区会被替换成 `{system prompt, prior summaries, new summary, live zone raw messages}`；
   - 然后发出 `compact_complete` 事件。

## 保持不变的约束

- **不会在轮次中途替换。** 对话只会在轮次之间被替换，所以控制器不会在一次 LLM 调用中途发现消息突然消失。
- **压缩期间活跃区不会变小。** 摘要任务还在跑的时候，新轮次会继续追加到活跃区，最终替换时会把这些新内容算进去。
- **摘要可以层层累积。** 下一次压缩会把上一次摘要也纳入进去，所以历史信息会逐步变粗，但不会直接丢掉。
- **可以按 creature 关闭。** 把 `compact.enabled: false` 设上，就会彻底禁用这个机制。

## 代码位置

- `src/kohakuterrarium/core/compact.py` —— `CompactManager`，里面有 start/pending/done 状态机。
- `src/kohakuterrarium/core/agent.py` —— `_init_compact_manager()`，在 `start()` 时把 manager 接到 agent 上。
- `src/kohakuterrarium/core/controller.py` —— 每轮结束后的 hook，会让 manager 判断是否要做压缩。
- `src/kohakuterrarium/builtins/user_commands/compact.py` —— 手动触发的 `/compact` 命令。

## 另见

- [Memory and compaction](/concepts/modules/memory-and-compaction.md)（英文）—— 概念层面的说明。
- [reference/configuration.md — `compact`](/reference/configuration.md)（英文）—— 每个 creature 可用的配置项。
