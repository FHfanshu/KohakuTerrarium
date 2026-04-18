# 非阻塞压缩

## 这个问题是什么

一个 creature 如果连续跑上几个小时，对话就会越积越多。到某个时刻，prompt 会超过模型能吃下的上下文上限。常见补救办法是 compaction：把旧轮次压成一段摘要，最近几轮仍然保留原文。

但 compaction 本身也要发起一次 LLM 调用。如果总结期间把 controller 卡住，那种常驻型 agent 会直接僵在那里，几十秒都没反应，只是为了把 50k token 重新写一遍。

对 coding-agent 风格的 creature，这还算能忍。对监控型或聊天型 creature，就不行了。

## 考虑过的方案

- **同步暂停。** 停下 controller，做完总结，再继续。简单，但卡顿明显。
- **交给单独的 agent。** 这件事说到底只是“把旧轮次改写成一段话”，专门起一个 agent 太重了。
- **后台任务 + 原子替换。** 总结在后台跑，controller 继续工作；等到轮次之间再把对话换掉。框架现在就是这么做的。

## 实际怎么做

概念上，对话会分成两个区：

```
  [ ----- 压缩区 ----- ][ --- 活跃区（keep_recent_turns）--- ]
           可压缩                           保留原文，不做总结
```

流程是这样：

1. 每轮结束后，compact manager 检查
   `prompt_tokens >= threshold * max_tokens`。
2. 如果满足条件，就发一个 `compact_start` 活动事件，并启动后台 `asyncio.Task`。
3. 这个任务会：
   - 给压缩区做快照；
   - 调用总结用的 LLM；默认是主 controller 的 LLM，如果配置了更便宜的 `compact_model`，就用它；
   - 生成摘要，同时把决策、文件路径、错误字符串这类高信号 token 原样保留下来。
4. 这段时间 controller 不会停。工具照跑，sub-agent 可以继续启动，用户也能继续输入。
5. 摘要准备好后，manager 会等当前轮次结束，再**原子地**改写对话：
   - 旧压缩区会被替换成 `{system prompt, prior summaries, new summary, live zone raw messages}`；
   - 然后发出 `compact_complete` 事件。

## 保住了哪些不变量

- **不会在轮次中途替换。** 对话只会在轮次之间被替换，所以 controller 不会在一次 LLM 调用中途发现消息突然没了。
- **压缩期间活跃区不会变小。** 摘要任务还在跑时，新轮次会继续追加到活跃区；真正替换时会把这些内容算进去。
- **摘要会一层层累积。** 下一次 compaction 会把上一次摘要也带上，所以历史会逐渐变粗，但不会直接丢。
- **可以按 creature 关闭。** `compact.enabled: false` 会彻底禁用这个机制。

## 代码在哪

- `src/kohakuterrarium/core/compact.py` —— `CompactManager`，里面有 start/pending/done 状态机。
- `src/kohakuterrarium/core/agent.py` —— `_init_compact_manager()`，在 `start()` 时把 manager 接到 agent 上。
- `src/kohakuterrarium/core/controller.py` —— 每轮结束后的 hook，会让 manager 判断要不要压缩。
- `src/kohakuterrarium/builtins/user_commands/compact.py` —— 手动触发的 `/compact` 命令。

## 另见

- [Memory and compaction](../modules/memory-and-compaction.md) —— 概念层面的说明。
- [reference/configuration.md — `compact`](../../reference/configuration.md) —— 每个 creature 可用的配置项。
