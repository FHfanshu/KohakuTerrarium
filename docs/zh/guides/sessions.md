# Sessions

给需要保存、恢复或归档 agent 运行记录的人看。

session 会把一次运行的状态打包成一个 `.kohakutr` 文件，里面包括对话、事件、子 agent 对话、channel 历史、scratchpad、jobs、可恢复 trigger，以及配置元数据。你可以在任意时刻停下 creature，之后从原来的位置继续。

概念预读：[memory and compaction](/concepts/modules/memory-and-compaction.md)（英文）、[session and environment](/concepts/modules/session-and-environment.md)（英文）。

## `.kohakutr` 文件

`.kohakutr` 是一个 SQLite 数据库（通过 KohakuVault），里面有 9 张表：

| 表 | 用途 |
|---|---|
| `meta` | session 元数据、配置快照、terrarium 拓扑 |
| `state` | 每个 agent 的 scratchpad、turn 计数、累计 token 用量、可恢复 trigger |
| `events` | 追加写入的日志，记录每个文本 chunk、tool call、trigger、token 使用事件 |
| `channels` | 按 channel 名称保存的消息历史 |
| `subagents` | 子 agent 对话快照，按 parent + name + run 作为键 |
| `jobs` | tool 和子 agent 的 job 记录 |
| `conversation` | 每个 agent 最新的对话快照，用于快速恢复 |
| `fts` | `events` 上的 FTS5 索引，供 `kt search` 使用 |
| `vectors` | 可选的 embedding 列，由 `kt embedding` 填充 |

事件数据采用追加写入，版本由 KohakuVault 的 auto-pack 管理。`.kohakutr` 文件可以直接复制、归档或发邮件，不依赖外部文件。

## session 存在哪里

```text
~/.kohakuterrarium/sessions/<name>.kohakutr
```

`<name>` 默认由 creature 或 terrarium 名称加时间戳自动生成。你也可以用 `--session <path>` 指定路径，或者用 `--no-session` 关闭。

## 会保存什么

每一轮运行，KohakuTerrarium 会记录这些内容：

- **对话快照**：用 msgpack 保存原始 message dict。会保留 `tool_calls`、多模态内容和元数据。
- **事件日志**：每个 chunk、tool call、子 agent 输出、trigger 触发、channel 消息、compact、interrupt 或 error 都有一条记录。这是最终依据的历史。
- **子 agent 对话**：在子 agent 销毁前保存，所以事后还能查看它做了什么。
- **scratchpad 和 channel 消息**：分别按 agent 和 channel 保存。
- **job 记录**：长时间运行的 tool 和子 agent 输出。
- **可恢复 trigger**：任何 `resumable: True` 的 `BaseTrigger` 子类都会序列化到 `state`，恢复时再还原。
- **配置快照**：运行时完整解析后的配置。即使磁盘上的配置后来改了，恢复时也能重建 agent。

## 恢复运行

```bash
kt resume --last            # 最近一次 session
kt resume                   # 交互式选择器（显示最近 10 条）
kt resume my-agent_20240101 # 按名称前缀
kt resume ~/backup/run.kohakutr
```

恢复会自动判断类型：agent session 会挂载单个 creature；terrarium session 会恢复整套连线，并强制使用 TUI 模式。

可用参数和 `kt run` 基本一样：`--mode`、`--llm`、`--log-level`，另外还有 `--pwd <dir>` 用来覆盖工作目录。

恢复时会做这些事：

1. 从 `meta` 读取配置快照。
2. 重新加载当前磁盘上的配置，这样你后来改过的 prompt 或 tool 会生效。
3. 合并两者：配置快照决定 session 身份，当前配置决定运行逻辑。
4. 重建 agent，挂回同一个 `SessionStore`，重新注入对话快照，重放 scratchpad、channel 和 trigger 状态。
5. 重新启动 controller；之前的事件仍然在上下文里。

所以，小的配置漂移通常没问题，比如换 LLM、改 prompt。结构性的变化就可能出错，比如改了 creature 名称，或者删掉了它当时正在用的 tool。要完全一致，最好把 session 绑在原始配置上。

## 中断再恢复的流程

```bash
kt run @kt-defaults/creatures/swe
# 做事……然后 Ctrl+C
# 之后：
kt resume --last
```

按 Ctrl+C 时，agent 会尽量正常退出：先完成手头的 tool，刷新 session store，再打印恢复提示。强制杀掉进程（SIGKILL）不会执行最后一次 flush，但因为是追加写入，最近的大部分状态通常已经落盘。

## 复制或归档 session

```bash
# 备份
cp ~/.kohakuterrarium/sessions/swe_20240101.kohakutr ~/backups/

# 从移动后的路径恢复
kt resume ~/backups/swe_20240101.kohakutr

# 不完整恢复、只做查看（只读 CLI 之后会补；现在先用 Python）
```

用代码查看：

```python
from kohakuterrarium.session.store import SessionStore
store = SessionStore("~/backups/swe_20240101.kohakutr")
print(store.load_meta())
for agent, event in store.get_all_events():
    print(agent, event["type"])
store.close()
```

## Compaction

当上下文快满时，compaction 会压缩对话。可以按 creature 配置：

```yaml
compact:
  enabled: true
  threshold: 0.8              # 上下文达到窗口的 80% 时开始压缩
  target: 0.5                 # 压缩后尽量降到 50%
  keep_recent_turns: 5        # 最近 N 轮始终原样保留
  compact_model: gpt-4o-mini  # 用更便宜的模型做总结
```

compaction 在后台跑，见 [concepts/modules/memory-and-compaction](/concepts/modules/memory-and-compaction.md)（英文）。controller 不会停；新摘要准备好之后，会替换当前对话。每次 compaction 都会记成一条事件。

手动触发 compaction：

```text
/compact
```

在 CLI 或 TUI 提示符里输入即可。要把一个很长的 session 交给别人，或者把它当上下文塞进另一轮运行前，这个命令很实用。

## Memory search

session 也可以当可搜索的知识库。先建索引：

```bash
kt embedding ~/.kohakuterrarium/sessions/swe.kohakutr
kt search swe "auth bug"
```

agent 自己也能通过 `search_memory` tool 搜索。完整说明见 [Memory](/guides/memory.md)（英文）。

## 关闭持久化

有时候你只想跑一次，不留记录：

```bash
kt run @kt-defaults/creatures/swe --no-session
```

这样不会创建 `.kohakutr`。同时也会失去 compaction 从磁盘恢复前几轮内容的能力，不过它仍然会在内存里压缩。

## 排错

- **Compaction 一直跑不完 / OOM。** `compact_model` 用的还是和 controller 一样的重模型。改成便宜一点的，比如 `gpt-4o-mini`、`claude-haiku`。
- **恢复时报 `tool not registered`。** creature 配置变了，某个 tool 被删掉了，但对话里还在引用它。手动改 `config.yaml` 把 tool 加回去，或者直接开一个新 session。
- **`kt resume` 找不到刚才看到的 session。** session 是按 `~/.kohakuterrarium/sessions/` 里的文件名前缀匹配的。如果你改过文件名或挪了位置，就传完整路径。
- **`.kohakutr` 文件太大。** 事件日志只追加不裁剪，session 跑得久就会一直长。旧文件可以归档，或者把工作拆成多个 session。compaction 只会缩小当前对话，不会删掉供搜索使用的完整事件历史。
- **恢复后看不到子 agent 输出。** 子 agent 对话是在它完成时保存的。如果父 agent 在子 agent 还没结束时被中断，最新快照只会是上一次 checkpoint 已经写入的内容。

## 另见

- [Memory](/guides/memory.md)（英文）— session 历史上的 FTS、语义搜索和混合搜索。
- [Configuration](/guides/configuration.md)（英文）— compaction 配方和 session 参数。
- [Programmatic Usage](/guides/programmatic-usage.md)（英文）— 自定义查看时使用的 `SessionStore` API。
- [Concepts / memory and compaction](/concepts/modules/memory-and-compaction.md)（英文）— compaction 的工作方式。
