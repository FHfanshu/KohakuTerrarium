# 会话持久化

## 这个设计要解决什么问题

一个 creature 的历史记录有三种使用方，需求并不一样：

1. **恢复运行。** 崩溃之后，或者执行 `kt resume --last` 之后，我们得尽快把 agent 的状态重建出来。所以可序列化的数据越少越好。
2. **人工检索。** 用户执行 `kt search <session> <query>` 时，会希望能对所有细节做关键词搜索和语义搜索。
3. **Agent 侧 RAG。** 运行中的 agent 会在单轮处理中调用 `search_memory`，它也需要同样的搜索能力。

同一套存储必须同时服务这三种场景。结构选错了，至少有一种会变得很贵，甚至做不成。

## 考虑过的方案

- **只存对话日志。** 恢复很便宜；搜索很差，因为没有工具活动、触发器触发记录，也没有子 agent 的输出。
- **只存完整事件日志，不做快照。** 搜索很好；恢复很慢，因为必须重放全部事件。
- **只存快照。** 恢复很快；但没有可搜索的历史。
- **双存储：追加式事件日志 + 每轮对话快照。** 我们现在就是这么做的。

## 实际做法

`.kohakutr` 文件本质上是一个 SQLite 数据库（通过 KohakuVault 管理），包含这些表：

- `events` —— 所有事件的追加式日志，包括文本分块、工具调用、工具结果、触发器触发、频道消息、token 用量。永远不会改写。
- `conversation` —— 每个 `(agent, turn-boundary)` 一行，保存消息列表快照（使用 msgpack，可保留 tool-call 结构）。
- `state` —— scratchpad 和每个 agent 的计数器。
- `channels` —— 频道消息历史。
- `subagents` —— 已生成子 agent 的对话快照，在销毁前保存。
- `jobs` —— 工具或子 agent 的执行记录，包括状态、参数、结果。
- `meta` —— 会话元数据、配置路径、运行标识。
- `fts` —— 基于 SQLite FTS5 的 `events` 索引，用于关键词搜索。
- 向量索引（可选，同样放在这个存储里）—— 在需要时由 `kt embedding` 构建。

### 恢复路径

1. 读取 `meta`，拿到 session id、配置路径、creature 列表。
2. 读取 `conversation[agent]` 快照，重建 agent 的 `Conversation` 对象。
3. 读取 `state[agent]:*`，恢复 scratchpad。
4. 读取 `type == "trigger_state"` 的事件，通过 `from_resume_dict` 重新创建触发器。
5. 将事件重放给输出模块的 `on_resume`，为 TTY 用户补回滚动历史。
6. 读取 `subagents[parent:name:run]`，重新挂回子 agent 的对话。

### 搜索路径

- FTS 模式：对 `events` 做 FTS5 匹配，按顺序返回结果块。
- 语义模式：做向量搜索，返回最近邻事件。
- 混合模式：做 rank-fuse。
- 自动模式：如果有向量索引就用语义搜索，否则用 FTS。

### Agent 侧 RAG

内建工具 `search_memory` 调用的就是 CLI 使用的那一层搜索逻辑。它会在需要时按 agent 名过滤、截断命中结果，然后把结果作为工具返回值交回去。

## 保持不变的约束

- **事件不可变。** 只能追加。
- **快照按轮保存。** 不是按事件保存。恢复相对于快照是 O(1)，而不是相对于整段历史的 O(N)。
- **不可序列化状态从配置重建。** 像 socket、pywebview 句柄、LLM provider session 这些，都会重新创建，不会从存储里直接恢复。
- **每个 session 一个文件。** 便于携带和复制；`.kohakutr` 扩展名也方便工具识别。
- **恢复是可关闭的默认能力。** `--no-session` 会彻底禁用这套存储。

## 代码里对应的位置

- `src/kohakuterrarium/session/store.py` —— `SessionStore` API。
- `src/kohakuterrarium/session/output.py` —— `SessionOutput` 通过 `OutputModule` 协议记录事件，所以控制器这一层不需要额外处理。
- `src/kohakuterrarium/session/resume.py` —— 重建路径。
- `src/kohakuterrarium/session/memory.py` —— FTS 和向量查询。
- `src/kohakuterrarium/session/embedding.py` —— embedding provider。

## 另见

- [Memory and compaction（英文）](/docs/concepts/modules/memory-and-compaction.md) —— 相关概念图景。
- [reference/cli.md — kt resume, kt search, kt embedding（英文）](/docs/reference/cli.md) —— 面向用户的入口。
