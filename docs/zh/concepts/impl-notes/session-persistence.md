# 会话持久化

## 这个问题是什么

一个 creature 的历史，要同时服务三类使用者，而且三边要的东西不一样：

1. **恢复运行。** 崩溃之后，或者执行 `kt resume --last` 之后，我们得尽快把 agent 状态重建出来。最好只序列化最少的一部分。
2. **人工搜索。** 用户执行 `kt search <session> <query>`，会希望能对所有细节做关键词搜索和语义搜索。
3. **Agent 侧 RAG。** 正在运行的 agent 会在轮次里调用 `search_memory`，也希望拿到同样的搜索能力。

同一个存储层得同时扛住这三件事。结构选错了，总会有一边变得很贵，甚至做不了。

## 考虑过的方案

- **只存对话日志。** 恢复很便宜；搜索却很差，因为里面没有工具活动、trigger 触发、sub-agent 输出这些东西。
- **只存完整事件日志，不做快照。** 搜索很好；恢复很慢，因为要把所有事件重新回放一遍。
- **只存快照。** 恢复快；但没有可搜索的历史。
- **双存储：只追加的事件日志 + 每轮对话快照。** 这就是现在的做法。

## 实际怎么做

`.kohakutr` 文件本质上是一个 SQLite 数据库（通过 KohakuVault 管理），里面有这些表：

- `events` —— 只追加的事件日志，记录每个事件（文本块、工具调用、工具结果、trigger 触发、channel 消息、token 用量）。不会重写。
- `conversation` —— 按 `(agent, turn-boundary)` 存每个快照点的消息列表（用 msgpack 保存，能保住 tool-call 结构）。
- `state` —— scratchpad 和每个 agent 的计数器。
- `channels` —— channel 消息历史。
- `subagents` —— 已生成 sub-agent 的对话快照，会在销毁前存下来。
- `jobs` —— 工具和 subagent 的执行记录（状态、参数、结果）。
- `meta` —— session 元数据、配置路径、运行标识符。
- `fts` —— 基于 SQLite FTS5 的 `events` 索引，用来做关键词搜索。
- 向量索引（可选，也放在同一个存储里）—— 需要时通过 `kt embedding` 构建。

### 恢复路径

1. 读取 `meta`，拿到 session id、配置路径、creature 列表。
2. 读取 `conversation[agent]` 快照，重建 agent 的 `Conversation` 对象。
3. 读取 `state[agent]:*`，恢复 scratchpad。
4. 读取 `type == "trigger_state"` 的事件，通过 `from_resume_dict` 重建 trigger。
5. 把事件回放给 output module 的 `on_resume`，给 TTY 用户补出 scrollback。
6. 读取 `subagents[parent:name:run]`，把 sub-agent 的对话重新挂回去。

### 搜索路径

- FTS 模式：在 `events` 的 FTS5 索引里匹配，按顺序返回结果块。
- 语义模式：做向量搜索，返回最近的事件。
- 混合模式：做 rank-fuse。
- 自动模式：有向量就走语义，没有就走 FTS。

### Agent 侧 RAG

内置工具 `search_memory` 调用的就是 CLI 用的那一层搜索逻辑。它可以按 agent 名过滤，截断结果，再把命中项当作工具结果返回。

## 保住了哪些不变量

- **事件是不可变的。** 只会追加。
- **快照按轮次保存。** 不是按事件保存。恢复时面对的是 O(1) 的快照，而不是 O(N) 的整段历史。
- **不能序列化的状态会从配置重建。** 像 socket、pywebview handle、LLM provider session 这些东西，会重新创建，不会直接恢复。
- **每个 session 一个文件。** 好拷贝，也方便携带；`.kohakutr` 扩展名也让工具能认出来。
- **恢复功能可以关闭。** `--no-session` 会彻底禁用这个存储层。

## 代码在哪

- `src/kohakuterrarium/session/store.py` —— `SessionStore` API。
- `src/kohakuterrarium/session/output.py` —— `SessionOutput` 通过 `OutputModule` 协议记录事件，所以 controller 层不用为此做特殊处理。
- `src/kohakuterrarium/session/resume.py` —— 负责重建路径。
- `src/kohakuterrarium/session/memory.py` —— FTS 和向量查询。
- `src/kohakuterrarium/session/embedding.py` —— embedding provider。

## 另见

- [Memory and compaction](../modules/memory-and-compaction.md) —— 概念层面的说明。
- [reference/cli.md — `kt resume`, `kt search`, `kt embedding`](../../reference/cli.md) —— 用户能直接接触到的命令入口。
