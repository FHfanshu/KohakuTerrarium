# 会话、审计与排错



经常有人搞混这三种"痕迹"。这篇帮你看清楚：

| 类型 | 存在哪 | 用来干嘛 |
|------|--------|----------|
| `.kohakutr` session | `~/.kohakuterrarium/sessions/` | 恢复现场、搜索历史 |
| 审计日志 JSONL | creature 目录下的 `artifacts/audit/` | 人看、脚本分析、团队审计 |
| 服务日志 | `~/.kohakuterrarium/app.log` 或 `kt serve logs` | 排查故障 |

## 文件到底在哪

默认都在这个目录下：

```text
~/.kohakuterrarium/
```

如果你是 Windows 用户，通常就是：

```text
C:\Users\你的用户名\.kohakuterrarium\
```

想直接打开的话：

```powershell
explorer $env:USERPROFILE\.kohakuterrarium
```

常见几个位置：

- session 文件：`%USERPROFILE%\.kohakuterrarium\sessions\`
- 服务日志：`%USERPROFILE%\.kohakuterrarium\app.log`
- 本地扩展示例 `swe_bio_agent` 的审计日志：项目里的 `examples/agent-apps/swe_bio_agent/creatures/swe_bio_agent/artifacts/audit/`

## session 是什么

KohakuTerrarium 每次运行都会保存一个 `.kohakutr` 文件。它不是简单的聊天记录，而是完整快照：

| 内容 | 说明 |
|------|------|
| event log | 所有事件的时序记录 |
| 工具调用和结果 | 每次 tool call 的参数和返回值 |
| 子智能体调用和结果 | subagent 的输入输出 |
| channel 消息 | 多智能体场景的通信记录 |
| conversation snapshots | 对话压缩快照 |
| config metadata | 当时用的配置 |

默认在这里：

```text
~/.kohakuterrarium/sessions/
├── 2024-01-15_10-30-00_swe_bio_agent.kohakutr
├── 2024-01-15_14-22-33_swe.kohakutr
└── ...
```

Windows 一般对应：

```text
C:\Users\你的用户名\.kohakuterrarium\sessions\
```

可以直接打开：

```powershell
explorer $env:USERPROFILE\.kohakuterrarium\sessions
```

## 恢复 session

```powershell
# 列出最近的，让你选
kt resume

# 直接接上最近那个
kt resume --last

# 按名字找
kt resume swe_bio_agent
```

成功的话会看到：

```
Resuming session: 2024-01-15_10-30-00_swe_bio_agent.kohakutr
Loaded 42 messages, 15 tool calls
Ready. Type your message:
```

## 搜索历史 session

```powershell
# 关键词搜
kt search "read AGENTS.md"

# 精确全文搜
kt search "blocked bash command" --mode fts

# 语义搜（理解意思，不一定要原词）
kt search "read rule file" --mode semantic
```

搜索结果大概这样：

```
Found 3 matches in session 2024-01-15_10-30-00_swe_bio_agent.kohakutr:
  [10:30:15] User: read AGENTS.md
  [10:30:18] Tool: read("AGENTS.md")
  [10:30:22] Result: # AGENTS.md content...
```

## 人工检查 session

项目自带了个脚本，方便深入看：

```powershell
# 看全部
python scripts/inspect_session.py ~/.kohakuterrarium/sessions/your_session.kohakutr --all

# 只看事件流
python scripts/inspect_session.py ~/.kohakuterrarium/sessions/your_session.kohakutr --events

# 只看子智能体调用
python scripts/inspect_session.py ~/.kohakuterrarium/sessions/your_session.kohakutr --subagents

# 搜特定内容
python scripts/inspect_session.py ~/.kohakuterrarium/sessions/your_session.kohakutr --search "worker"
```

## 审计日志

如果你使用的是带审计插件的本地扩展示例 creature，比如 `swe_bio_agent`，它还会额外写一份 JSONL，每行一条结构化记录：

```text
examples/agent-apps/swe_bio_agent/creatures/swe_bio_agent/artifacts/audit/
├── 2024-01-15_10-30-00.jsonl
└── ...
```

一条记录长这样：

```json
{"type": "agent_start", "timestamp": "2024-01-15T10:30:00", "data": {"session_id": "xxx", "working_dir": "/path/to/repo"}}
{"type": "tool_start", "timestamp": "2024-01-15T10:30:05", "data": {"tool": "read", "args": {"path": "AGENTS.md"}}}
```

用处：

| 场景 | 怎么用 |
|------|--------|
| 人复盘 | 文本编辑器直接看 |
| 脚本分析 | Python / jq 处理 JSONL |
| 团队审计 | 接到 SIEM 或告警系统 |

快速查看：

```powershell
# PowerShell
Get-Content audit.jsonl | ConvertFrom-Json

# 或者用 jq
cat audit.jsonl | jq .
```

## 服务日志

### 用 `kt serve` 跑的

```powershell
kt serve status    # 看状态
kt serve logs      # 看日志
kt serve logs -n 100  # 最近100行
```

### 用桌面应用的

崩溃的时候看这个：

```text
~/.kohakuterrarium/app.log
```

要更详细的日志：

```powershell
kt serve start --log-level DEBUG
# 或
kt run my-creature --log-level DEBUG
```

## 排错：一步步来

按这个顺序查，大问题基本能定位：

```
1. creature 没启动 → kt info my-creature/
2. 没有 session → ls ~/.kohakuterrarium/sessions/
3. 没有审计日志 → ls artifacts/audit/
4. 服务有问题 → kt serve logs / cat app.log
```

## 查什么？

| 你想干嘛 | 看什么 |
|----------|--------|
| 恢复中断的工作 | `kt resume` |
| 找之前聊过什么 | `kt search` |
| 审计操作记录 | JSONL 审计日志 |
| 服务端报错了 | `kt serve logs` |
| 桌面应用崩了 | `app.log` |
| 插件行为不对 | 加 `--log-level DEBUG` 重跑 |

## 常见问题

### session 文件太大

长会话 + 大量工具调用 = 文件膨胀。解法：

```yaml
# 开启上下文压缩
compact:
  enabled: true
  threshold: 100000
```

或者干脆不存：

```powershell
kt run my-creature --no-session
```

### 审计日志是空的

检查：

1. 配置里有没有 audit 插件
2. 输出目录是不是存在、有没有写权限
3. 如果你用的是 `swe_bio_agent` 这类本地扩展示例，再看下 `kt info examples/agent-apps/swe_bio_agent` 有没有显示 `Plugins: 2`

### `kt search` 搜不到东西

语义搜索需要 embedding 模型。没配的话用全文搜索：

```powershell
kt search "关键词" --mode fts
```

---


