# Memory and compaction

## 它是什么

这是两个彼此相关的系统：

- **Memory。** `.kohakutr` 会话文件既是运行时持久化存储，也是可搜索的知识库。每个事件都会被建立索引，用于全文检索（FTS5），也可以选择建立向量检索。Agent 在自身运行过程中可以通过 `search_memory` 工具查询这些内容。
- **Compaction。** 长时间运行的 creature 迟早会把上下文窗口撑满。自动压缩会在后台总结较早的轮次，不会暂停 controller，所以 agent 会继续工作，历史则被压缩成更短的形式。

两者其实都在回答同一个问题：creature 累积下来的历史，该怎么处理。

## 为什么需要它

### Memory

很多 agent 框架把历史当成临时数据：只服务当前这次 LLM 调用，最多为了“恢复运行”存一下，除此之外基本就丢了。这样会浪费很多有用信息。同一份事件日志，其实可以同时支持：

- `kt resume`：在任务做到一半时把 agent 重新构建出来。
- `kt search`：让人直接查看会话里发生过什么。
- agent 侧基于自身历史做 RAG（`search_memory`）。

一个存储，三种用法。

### Compaction

上下文窗口会变大，但增长速度永远追不上长时间运行的需求。不做压缩的话，一个连续跑了几个小时的 creature 迟早会撞上上限。最直接的压缩办法，是让 agent 停下来做总结；但在 agent 框架里，这就意味着 controller 会被冻结，眼看着 5 万 token 被浓缩成 2 千。对于常驻运行的 agent，这种停顿没法接受。

非阻塞压缩会在后台任务里完成总结，再在轮次之间用原子方式把结果接进去。controller 不会停。

## 我们怎么定义它

### Session store 的结构

`.kohakutr` 是一个 SQLite 文件（通过 KohakuVault 访问），里面有这些表：

- `meta` —— 会话元数据、快照、配置
- `events` —— 只追加的事件日志
- `state` —— 草稿区、计数器、每个 agent 的状态
- `channels` —— 消息历史
- `conversation` —— 用于快速恢复的最新快照
- `subagents` —— 子 agent 的会话快照
- `jobs` —— 工具和子 agent 的执行记录
- `fts` —— 事件上的全文索引
- （可选）向量索引，在生成 embedding 时建立

### Compaction 的约定

一个 creature 会有 `compact` 配置块，包含这些字段：`enabled`、`max_tokens`（或自动推导出的值）、`threshold`（达到预算的 N% 时开始压缩）、`target`（压缩到 N%）、`keep_recent_turns`（永远不总结的最近轮次区域），以及可选的 `compact_model`（更便宜的总结模型）。

每轮结束时，如果 `prompt_tokens >= threshold * max_tokens`，compact manager 就会启动一个后台任务。

## 我们怎么实现它

- `session/store.py` —— 基于 KohakuVault 的持久化存储。
- `session/output.py` —— 把事件写入存储的 output consumer。
- `session/resume.py` —— 把记录回放到一个新建的 agent 中。
- `session/memory.py` —— FTS5 查询和向量检索。
- `session/embedding.py` —— 负责 embedding 的 model2vec / sentence-transformer / API provider。
- `core/compact.py` —— 带有 atomic-splice 技巧的 `CompactManager`。见 [impl-notes/non-blocking-compaction](/concepts/impl-notes/non-blocking-compaction.md)（英文）。

Embedding provider（`kt embedding`）有这些：

- **model2vec**（默认，不需要 torch；预设包括 `@tiny`、`@best`、`@multilingual-best` 等）
- **sentence-transformer**（需要 torch）
- **api**（外部 embedding 端点，比如 jina-v5-nano）

## 因而你能做什么

- **从任意位置恢复。** `kt resume` / `kt resume --last` 可以接着一个几小时前中断的会话继续跑。
- **搜索会话。** `kt search <session> <query>` 支持 FTS、语义检索、混合检索，或自动判断模式。
- **让 agent 用自己的历史做 RAG。** agent 在某一轮里调用 `search_memory`，拿到相关的过往事件，再带着这些上下文继续往下做。
- **支撑长时间常驻运行。** 一个连续跑了几天的 creature 不会因为上下文上限停住；压缩会把滚动摘要放在前面，后面保留最近的 N 轮。
- **跨会话共享记忆。** 配置更复杂一点时，可以从配置里取出 session store 路径，让一组相关的 creature 共用同一份存储。

## 别被它框住

会话持久化默认开启，可用 `--no-session` 关闭。Embedding 默认不开。Compaction 对每个 creature 来说也是默认开启、可单独关闭。你当然也可以一个都不用——memory 只是方便，不是前提。

## 另见

- [impl-notes/session-persistence](/concepts/impl-notes/session-persistence.md)（英文）—— 双存储的细节。
- [impl-notes/non-blocking-compaction](/concepts/impl-notes/non-blocking-compaction.md)（英文）—— atomic-splice 算法。
- [reference/cli.md — kt embedding, kt search, kt resume](/reference/cli.md)（英文）—— 相关命令入口。
- [guides/memory.md](/guides/memory.md)（英文）—— 使用指南。
