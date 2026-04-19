# Sessions

给想把 agent 运行过程存下来、接着跑，或者归档的人看。

一次 session 会把这次运行里的状态打成一个 `.kohakutr` 文件：对话、事件、子 agent 对话、channel 历史、scratchpad、jobs、可恢复的 triggers，还有配置元数据都在里面。你随时都可以停掉一个 creature，之后再从原地接着跑。

先补概念： [memory and compaction](./concepts/modules/memory-and-compaction.md)、[session and environment](./concepts/modules/session-and-environment.md)。

## `.kohakutr` 文件是什么

`.kohakutr` 是一个 SQLite 数据库（通过 KohakuVault），里面有九张表：

| Table | Purpose |
|---|---|
| `meta` | session 元数据、配置快照、terrarium 拓扑 |
| `state` | 每个 agent 的 scratchpad、轮次计数、累计 token 用量、可恢复 triggers |
| `events` | 追加写入的事件日志：文本块、tool 调用、trigger、token 使用事件，全都记 |
| `channels` | 按 channel 名字存消息历史 |
| `subagents` | 子 agent 对话快照，键是 parent + name + run |
| `jobs` | tool 和 sub-agent 的任务记录 |
| `conversation` | 每个 agent 最新的对话快照，方便快速 resume |
| `fts` | 基于 events 的 FTS5 索引，给 `kt search` 用 |
| `vectors` | 可选的 embedding 列，跑 `kt embedding` 后会填上 |

这个格式对事件数据是 append-only，而且通过 KohakuVault 的 auto-pack 做版本管理。`.kohakutr` 文件可以直接复制、归档、发邮件，它不依赖别的外部文件。

## session 存哪里

```
~/.kohakuterrarium/sessions/<name>.kohakutr
```

`<name>` 会根据 creature / terrarium 名字加时间戳自动生成。你也可以用 `--session <path>` 指定路径，或者用 `--no-session` 直接不存。

## 会保存什么

每一轮 KohakuTerrarium 都会记这些东西：

- **对话快照** —— 原始 message dict，用 msgpack 存。`tool_calls`、多模态内容、各种元数据都保得住。
- **事件日志** —— 每个 chunk、tool 调用、sub-agent 输出、trigger 触发、channel 消息、compact、中断、错误，都会有一条记录。这才是最原始的历史。
- **子 agent 对话** —— 子 agent 被销毁前会先保存，所以事后还能回头看它到底干了什么。
- **Scratchpad 和 channel 消息** —— 按 agent、按 channel 分开存。
- **任务记录** —— 长时间运行的 tools 和 sub-agents 的输出。
- **可恢复 triggers** —— 任何 `BaseTrigger` 子类只要设了 `resumable: True`，就会序列化进 `state`，resume 时再恢复。
- **配置快照** —— 运行当下已经完全解析好的配置。这样即使磁盘上的配置后来改了，resume 也还能把 agent 重新搭起来。

## 恢复运行

```bash
kt resume --last            # 最近一次 session
kt resume                   # 交互式选择（会显示最近 10 个）
kt resume my-agent_20240101 # 按名字前缀找
kt resume ~/backup/run.kohakutr
```

resume 会自动判断类型：如果是普通 agent session，就挂一个 creature；如果是 terrarium session，就把整套 wiring 都挂起来，并强制进 TUI 模式。

可用参数和 `kt run` 一样：`--mode`、`--llm`、`--log-level`，再加一个 `--pwd <dir>` 用来覆盖工作目录。

resume 实际上做了这些事：

1. 从 `meta` 里读配置快照。
2. 重新加载磁盘上的当前配置，所以你后来改的 prompt / tool 设置也会生效。
3. 把两边合并：配置快照负责 session 身份；当前配置负责实际运行逻辑。
4. 重建 agent，挂上同一个 `SessionStore`，把对话快照重新注入，再恢复 scratchpad / channel / trigger 状态。
5. 用一个新的 controller 继续跑；之前的 events 还都在上下文里。

所以，小范围配置漂移一般没事，比如换个 LLM、改个 prompt。结构性的变化就可能出问题，比如 creature 改名了，或者删掉了它原本正在用的 tool。你如果要的是完全一致的恢复，那最好把 session 绑定回它最初那份配置。

## 中断后再继续

```bash
kt run @kt-biome/creatures/swe
# work... then Ctrl+C
# later:
kt resume --last
```

按 Ctrl+C 时，agent 会尽量正常退出：把正在跑的 tool 收尾、把 session store 刷盘，然后打印一条 resume 提示。要是被强杀（SIGKILL），最后那次 flush 会来不及，但因为写入是 append-only，大部分最新状态通常还是已经在盘上了。

## 复制或归档 session

```bash
# 备份
cp ~/.kohakuterrarium/sessions/swe_20240101.kohakutr ~/backups/

# 从移动后的位置恢复
kt resume ~/backups/swe_20240101.kohakutr

# 不完整恢复，只做查看（只读 CLI 以后会补；现在先用 Python）
```

代码里直接看：

```python
from kohakuterrarium.session.store import SessionStore
store = SessionStore("~/backups/swe_20240101.kohakutr")
print(store.load_meta())
for agent, event in store.get_all_events():
    print(agent, event["type"])
store.close()
```

## Compaction

上下文快满的时候，compaction 会把对话压缩一下。按 creature 配：

```yaml
compact:
  enabled: true
  threshold: 0.8              # 上下文占到窗口 80% 时开始 compact
  target: 0.5                 # 压完尽量落到 50%
  keep_recent_turns: 5        # 最近 N 轮始终原样保留
  compact_model: gpt-4o-mini  # 总结这一步用便宜模型
```

Compaction 在后台跑（见 [concepts/modules/memory-and-compaction](./concepts/modules/memory-and-compaction.md)）。controller 不会停着等；新的摘要准备好之后，对话会切换过去。每次 compaction 也都会记成一条 event。

手动 compact：

```
/compact
```

在 CLI / TUI 输入框里敲就行。长 session 要交给别人，或者你想把它当上下文塞进另一轮运行前，这个命令很实用。

## Memory 搜索

Session 也可以当一个可搜索的知识库。先建索引：

```bash
kt embedding ~/.kohakuterrarium/sessions/swe.kohakutr
kt search swe "auth bug"
```

agent 自己也能通过 `search_memory` tool 去搜。完整说明看 [Memory](memory.md)。

## 关闭持久化

有时候你就是想跑一次性的：

```bash
kt run @kt-biome/creatures/swe --no-session
```

这样不会生成 `.kohakutr`。同时 compaction 也没法再从磁盘恢复前面的轮次，不过它还是会在内存里照样 compact。

## 排错

- **Compaction 一直跑不完 / OOM。** 你拿来做 compact 的模型和 controller 一样重。把 `compact_model` 换成便宜点的，比如 `gpt-4o-mini`、`claude-haiku`。
- **Resume 报 `tool not registered`。** creature 配置变了，某个 tool 被删了，但历史对话里还在引用它。要么手动改 `config.yaml` 把 tool 加回来，要么直接开一个新 session。
- **`kt resume` 找不到刚才还看见的 session。** session 是按 `~/.kohakuterrarium/sessions/` 下面的文件名前缀匹配的。如果你改过文件名或者移过位置，就传完整路径。
- **`.kohakutr` 文件很大。** 事件日志是 append-only，session 跑久了肯定会涨。旧的归档掉，或者把工作拆成多个 session。Compaction 只能缩小当前对话，不会删完整事件历史，因为搜索还要靠它。
- **Resume 后看不到子 agent 输出。** 子 agent 对话是在它完成时保存的。如果父 agent 是在子 agent 运行到一半时被打断，那你能拿到的就是上一个 checkpoint 时已经存下来的快照。

## 另见

- [Memory](memory.md) —— 在 session 历史上做 FTS、语义搜索和混合搜索。
- [Configuration](configuration.md) —— compaction 配法和 session 参数。
- [Programmatic Usage](programmatic-usage.md) —— 自定义查看时用的 `SessionStore` API。
- [Concepts / memory and compaction](./concepts/modules/memory-and-compaction.md) —— compaction 是怎么工作的。