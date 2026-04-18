# 会话、审计与排错

智能体跑起来之后会留下几种"痕迹"。很多人搞混它们，这篇帮你分清楚：

| 类型 | 存在哪 | 有什么用 |
|------|--------|----------|
| session 文件（`.kohakutr`） | `~/.kohakuterrarium/sessions/` | 恢复中断的工作、搜索历史记录 |
| 审计日志（JSONL） | creature 目录下的 `artifacts/audit/` | 人复盘、脚本分析、团队审计 |
| 服务日志 | `~/.kohakuterrarium/app.log` 或 `kt serve logs` | 排查故障 |

简单说：
- **session** 是给机器用的，用来恢复现场
- **审计日志** 是给人和脚本用的，用来复盘和分析
- **服务日志** 是给开发者用的，用来查 bug

## 文件都在哪

所有东西默认都在这个目录下：

```text
~/.kohakuterrarium/
```

Windows 用户就是：

```text
C:\Users\你的用户名\.kohakuterrarium\
```

想直接打开这个目录：

```powershell
explorer $env:USERPROFILE\.kohakuterrarium
```

具体位置：
- session 文件：`%USERPROFILE%\.kohakuterrarium\sessions\`
- 服务日志：`%USERPROFILE%\.kohakuterrarium\app.log`
- 如果你用了 `swe_bio_agent` 扩展示例，审计日志在：`examples/agent-apps/swe_bio_agent/creatures/swe_bio_agent/artifacts/audit/`

## session 文件是什么

每次运行智能体，KohakuTerrarium 都会保存一个 `.kohakutr` 文件。它不是简单的聊天记录，而是完整的运行快照——你可以在任意时刻停下来，之后再接上继续跑。

里面存了这些东西：

| 内容 | 说明 |
|------|------|
| 所有对话 | 用户说了什么、模型回了什么 |
| 所有工具调用 | 每次工具的参数和返回结果 |
| 子智能体调用 | 子智能体的输入输出 |
| channel 消息 | 多智能体场景下的通信记录 |
| scratchpad 状态 | 智能体的临时记忆 |
| 配置信息 | 当时用的 creature 配置 |

本质上它是一个 SQLite 数据库，你可以直接复制、归档、发给别人，没有任何外部依赖。

文件命名规则：`日期_时间_creature名.kohakutr`

```text
~/.kohakuterrarium/sessions/
├── 2024-01-15_10-30-00_swe_bio_agent.kohakutr
├── 2024-01-15_14-22-33_swe.kohakutr
└── ...
```

## 恢复 session

如果上次跑智能体时中途停了（Ctrl+C、关了窗口、或者崩溃了），可以恢复：

```powershell
# 列出最近的几个，让你选
kt resume

# 直接接上最近那个
kt resume --last

# 按名字找（只要前缀匹配就行）
kt resume swe_bio_agent

# 从指定路径恢复
kt resume ~/backups/old_session.kohakutr
```

恢复成功后会看到：

```
Resuming session: 2024-01-15_10-30-00_swe_bio_agent.kohakutr
Loaded 42 messages, 15 tool calls
Ready. Type your message:
```

恢复时会发生什么：
1. 读取 session 里存的配置
2. 重新加载当前的 creature 配置（所以你改过的 prompt/tool 会生效）
3. 把之前的对话历史塞回上下文
4. 从中断的地方继续

这意味着你可以改配置后恢复——比如换个模型、改个 prompt。但如果改动太大（删了正在用的工具），可能会出错。

## 搜索历史 session

你可以像搜文档一样搜之前的对话：

```powershell
# 按关键词搜
kt search "read AGENTS.md"

# 精确全文搜索
kt search "blocked bash command" --mode fts

# 语义搜索（理解意思，不一定要原词）
kt search "read rule file" --mode semantic
```

搜索结果：

```
Found 3 matches in session 2024-01-15_10-30-00_swe_bio_agent.kohakutr:
  [10:30:15] User: read AGENTS.md
  [10:30:18] Tool: read("AGENTS.md")
  [10:30:22] Result: # AGENTS.md content...
```

语义搜索需要先建索引：

```powershell
kt embedding ~/.kohakuterrarium/sessions/swe.kohakutr
kt search swe "auth bug"
```

## 中断和恢复的典型流程

```powershell
kt run @kt-defaults/creatures/swe
# 干活... 然后 Ctrl+C 停掉
# 过了一会：
kt resume --last
```

Ctrl+C 会让智能体优雅退出：先完成正在执行的工具调用，保存 session，然后打印恢复提示。如果是强制杀进程（SIGKILL），可能会丢掉最后一点状态，但大部分数据应该还在。

## 用代码查看 session

如果你想深入检查 session 内容：

```python
from kohakuterrarium.session.store import SessionStore

store = SessionStore("~/backups/swe_20240101.kohakutr")
print(store.load_meta())

for agent, event in store.get_all_events():
    print(agent, event["type"])

store.close()
```

## 审计日志是什么

如果你用的是带审计插件的 creature（比如 `swe_bio_agent`），它还会额外写一份 JSONL 文件。每行是一条结构化记录，方便人看或者脚本分析。

位置：

```text
examples/agent-apps/swe_bio_agent/creatures/swe_bio_agent/artifacts/audit/
├── swe_bio_agent_2024-01-15_10-30-00.jsonl
└── ...
```

一条记录长这样：

```json
{"event": "agent_start", "ts": "2024-01-15T10:30:00", "session_id": "xxx", "working_dir": "/path/to/repo"}
{"event": "tool_start", "ts": "2024-01-15T10:30:05", "tool_name": "read", "args": {"path": "AGENTS.md"}}
{"event": "tool_end", "ts": "2024-01-15T10:30:06", "success": true}
```

审计日志的用途：

| 场景 | 怎么用 |
|------|--------|
| 自己复盘 | 用文本编辑器直接看 |
| 写脚本分析 | 用 Python 或 jq 处理 JSONL |
| 团队审计需求 | 接到 SIEM 或告警系统 |

快速查看：

```powershell
# PowerShell
Get-Content audit.jsonl

# 用 jq 格式化
cat audit.jsonl | jq .
```

## 服务日志

### 后台服务日志

如果你用 `kt serve` 跑后台服务：

```powershell
kt serve status       # 看服务状态
kt serve logs         # 看日志
kt serve logs -n 100  # 最近100行
```

### 桌面应用日志

如果桌面应用崩了，看这个：

```text
~/.kohakuterrarium/app.log
```

### 开启详细日志

排错时可以开 debug 级别：

```powershell
kt serve start --log-level DEBUG
# 或者
kt run my-creature --log-level DEBUG
```

## 对话太长了怎么办（Compaction）

长会话 + 大量工具调用 = session 文件会变大。框架有压缩机制，可以自动把老对话压缩成摘要：

```yaml
# 在 creature 配置里开启
compact:
  enabled: true
  threshold: 0.8       # 上下文用到 80% 时触发压缩
  target: 0.5          # 压缩到 50%
  keep_recent_turns: 5 # 保留最近 5 轮不压缩
  compact_model: gpt-4o-mini  # 用便宜的模型做压缩
```

压缩在后台跑，不影响当前对话。压缩完会自动把老对话换成摘要。

也可以手动触发：

```
/compact
```

在对话界面输入 `/compact`，适合在交接工作或把 session 发给别人之前用。

## 不想保存 session 怎么办

有时候只是想快速试一下，不想留痕迹：

```powershell
kt run my-creature --no-session
```

这样就不会创建 `.kohakutr` 文件。但压缩功能也没法从磁盘恢复之前的内容了。

## 排错流程

遇到问题按这个顺序查：

1. **creature 没启动** → `kt info my-creature/`
2. **没有 session 文件** → `ls ~/.kohakuterrarium/sessions/`
3. **没有审计日志** → `ls artifacts/audit/`
4. **服务有问题** → `kt serve logs` 或看 `app.log`
5. **插件行为不对** → 加 `--log-level DEBUG` 重跑

## 你想干嘛，看什么

| 你的需求 | 查看方式 |
|----------|----------|
| 恢复中断的工作 | `kt resume` |
| 找之前聊过什么 | `kt search` |
| 审计操作记录 | 看 JSONL 审计日志 |
| 服务端报错了 | `kt serve logs` |
| 桌面应用崩了 | 看 `app.log` |
| 插件行为奇怪 | 加 `--log-level DEBUG` 重跑 |

## 常见问题

### session 文件太大

长会话 + 大量工具调用 = 文件膨胀。解法：

```yaml
# 开启压缩
compact:
  enabled: true
  compact_model: gpt-4o-mini  # 用便宜的模型
```

或者干脆不保存：

```powershell
kt run my-creature --no-session
```

### 审计日志是空的

检查几件事：

1. creature 配置里有没有审计插件
2. 输出目录是否存在、有没有写权限
3. 如果你用的是 `swe_bio_agent`，看 `kt info examples/agent-apps/swe_bio_agent` 有没有显示 `Plugins: 2`

### `kt search` 搜不到东西

语义搜索需要 embedding 模型。没配的话用全文搜索：

```powershell
kt search "关键词" --mode fts
```

### 恢复时报错 `tool not registered`

creature 配置改了（删了某个工具），但历史对话里还在调用它。要么把工具加回去，要么开新 session。

### 压缩跑太慢或内存爆了

压缩用的模型太大了。设一个便宜的小模型：

```yaml
compact:
  compact_model: gpt-4o-mini  # 或 claude-haiku
```

---

[定制 SWE 智能体 ←](swe-bio-agent)