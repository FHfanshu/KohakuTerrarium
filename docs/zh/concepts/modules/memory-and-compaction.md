# Memory and compaction

## 它是什么

这是两套挨得很近的系统：

- **Memory。** `.kohakutr` session 文件既是运行时持久化，也是可搜索的知识库。每个事件都会建索引，支持全文检索（FTS5），也可以按需加上向量检索。agent 在自己内部就能通过 `search_memory` tool 查这些内容。
- **Compaction。** 跑得久了，creature 早晚会撞上上下文窗口上限。自动 compaction 会在后台总结旧 turn，而且不会把 controller 卡住。agent 一边继续工作，一边把旧上下文压缩掉。

这两件事其实都在回答同一个问题：**creature 累积下来的历史，到底怎么处理？**

## 为什么要有它

### Memory

很多 agent 框架把历史只当临时材料：给当前这次 LLM 调用用一下，最多为了“恢复运行”顺手持久化，别的就不管了。这样会丢很多信息。其实同一份事件日志，可以同时服务三种场景：

- `kt resume`：把中断的 agent 接着跑起来；
- `kt search`：让人回头查之前发生了什么；
- agent 自己对历史做 RAG，也就是 `search_memory`。

一份存储，三种消费方式。

### Compaction

上下文窗口一直在变大，但永远不够快。没有 compaction，跑上几个小时的 creature 迟早会顶到天花板。最笨的 compaction 做法，是一边总结一边暂停 agent；在 agent 框架里，这就等于 controller 卡死，眼看着 50k token 被揉成 2k。这对 ambient agent 来说很难接受。

non-blocking compaction 会把总结工作放到后台 task 里做，再在两个 turn 之间原子地把结果接进去。controller 不用停。

## 怎么定义它

### Session store 的形状

`.kohakutr` 是一个 SQLite 文件（通过 KohakuVault），里面有这些表：

- `meta` —— session 元数据、snapshot、配置
- `events` —— 只追加的事件日志
- `state` —— scratchpad、计数器、每个 agent 的状态
- `channels` —— 消息历史
- `conversation` —— 用于快速 resume 的最新快照
- `subagents` —— sub-agent 的会话快照
- `jobs` —— tool / subagent 的执行记录
- `fts` —— 事件上的全文索引
- （可选）向量索引，只有在构建 embeddings 时才有

### Compaction contract

creature 有一个 `compact` 配置块，里面包括：`enabled`、`max_tokens`（或自动推导）、`threshold`（达到预算 N% 时开始 compaction）、`target`（压到 N% 为止）、`keep_recent_turns`（永远不总结的最近活动区），还可以选填 `compact_model`（更便宜的总结模型）。

每个 turn 结束时，如果 `prompt_tokens >= threshold * max_tokens`，compact manager 就会起一个后台任务。

## 怎么实现它

- `session/store.py` —— 基于 KohakuVault 的持久化存储。
- `session/output.py` —— 把事件写入存储的 output consumer。
- `session/resume.py` —— 把历史重放到一个新建 agent 里。
- `session/memory.py` —— FTS5 查询和向量检索。
- `session/embedding.py` —— model2vec / sentence-transformer / API provider 的 embeddings。
- `core/compact.py` —— 带原子拼接技巧的 `CompactManager`。细节见 [impl-notes/non-blocking-compaction](/zh/concepts/impl-notes/non-blocking-compaction.md)。

embedding provider（`kt embedding`）有这些：

- **model2vec**（默认，不需要 torch；预设有 `@tiny`、`@best`、`@multilingual-best` 等）
- **sentence-transformer**（需要 torch）
- **api**（外部 embedding 接口，比如 jina-v5-nano）

## 你能拿它做什么

- **从任何地方恢复。** `kt resume` / `kt resume --last` 可以把几小时前中断的 session 接上。
- **查 session。** `kt search <session> <query>` 支持 FTS、语义检索、混合检索，或者自动判断模式。
- **agent 自己做 RAG。** agent 在一个 turn 里调用 `search_memory`，拿到相关旧事件，再带着这些上下文继续往下走。
- **长时间后台运行。** creature 连跑几天也不一定撞墙；compaction 会让滚动摘要压在最近 N 个 turn 上面。
- **跨 session 记忆。** 更复杂的配置可以把 session store 路径提出来，让一组相关 creature 共用。

## 别把它看得太死

session 持久化可以关掉（`--no-session`）。embeddings 是可选的。compaction 也是按 creature 选择开启或关闭。一个 creature 完全可以什么都不用；memory 是方便，不是前提。

## 另见

- [impl-notes/session-persistence](/zh/concepts/impl-notes/session-persistence.md) —— 双存储的细节。
- [impl-notes/non-blocking-compaction](/zh/concepts/impl-notes/non-blocking-compaction.md) —— 原子拼接算法。
- [reference/cli.md — kt embedding, kt search, kt resume](/zh/reference/cli.md) —— 命令入口。
- [guides/memory.md](/zh/guides/memory.md) —— 实操说明。
