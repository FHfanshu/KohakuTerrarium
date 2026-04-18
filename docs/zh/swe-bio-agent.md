# 定制 SWE 智能体



这篇对应的示例代码是：`examples/agent-apps/swe_bio_agent`

先说明一下：它是一个**本地扩展示例**，不是官方远端仓库当前默认自带的 creature。

- 如果你的工作区里有这个目录，这篇可以直接照着跑
- 如果没有这个目录，这篇依然可以当成"如何基于默认 `@kt-defaults/creatures/swe` 自己做增强版"的参考

它不是要替代默认 `swe`，而是在默认 `swe` 上加两个能力：

- **读规则**：进了仓库，必须先读完规则文件才让改代码
- **留痕迹**：所有重要操作都记 JSONL 日志，方便事后复盘

## 目录结构

```text
examples/agent-apps/swe_bio_agent/
  config.yaml           # 主配置
  prompts/
    system.md           # 系统提示词
  custom/
    guard_plugin.py     # 硬约束插件
    audit_plugin.py     # 审计插件
  artifacts/
    audit/              # 日志输出目录
```

## 它是怎么设计的

### 1. 继承默认 `swe`

```yaml
base_config: "@kt-defaults/creatures/swe"
```

好处很明显：

| 好处 | 说明 |
|------|------|
| 跟着升级 | 默认 `swe` 更新了，你自动受益 |
| 配置少 | 不用抄一整份工具列表 |
| 只管增量 | 只需要加"约束"和"留痕"两块 |

### 2. 用 prompt 说清楚规则

`prompts/system.md` 告诉模型：

- 进了仓库先读 `AGENTS.md`、`CLAUDE.md`、`CONTRIBUTING.md`、`README.md`
- 没读完之前，不许直接改代码
- 规则冲突时，优先更具体、更靠近当前目录的
- 保持默认 `swe` 的工作方式，别退化成纯聊天

### 3. 用 Guard 插件做硬拦截

prompt 只是"引导"，模型可能不听话。`custom/guard_plugin.py` 才是"硬核"的：

| 什么时候 | 拦什么 |
|----------|--------|
| 规则没读完 | `write`、`edit`、`multi_edit` |
| 规则没读完 | `worker` 子智能体 |
| 总是 | `git reset --hard`、`git clean -fd`、`rm -rf` |

设计思路就八个字：**prompt 引导，plugin 硬拦**。两层一起，比只写 prompt 稳得多。

### 4. 用 Audit 插件记日志

`custom/audit_plugin.py` 把这些信息写进 JSONL：

| 事件 | 记什么 |
|------|--------|
| `agent_start` | 启动时间、session id、工作目录 |
| `rules_found` | 发现了哪些规则文件 |
| `user_input` | 用户输的什么 |
| `tool_start/end` | 工具调用参数和结果 |
| `rules_read` | 规则文件读完了 |
| `subagent_start/end` | 子智能体调用和返回 |
| `agent_stop` | 结束时间 |

## 怎么跑

```powershell
# 命令行模式（在仓库根目录下，且目录存在）
kt run examples/agent-apps/swe_bio_agent --mode cli

# 全屏模式
kt run examples/agent-apps/swe_bio_agent --mode tui

# WebUI 模式
kt serve start
kt web
# 然后在界面里加载这个 creature
```

如果你手头没有这份本地扩展示例，就先跑默认 SWE：

```powershell
kt run @kt-defaults/creatures/swe --mode cli
```

## 跑完怎么看

```powershell
# 看有没有 session 文件
dir ~/.kohakuterrarium/sessions/*.kohakutr

# 看审计日志
dir examples/agent-apps/swe_bio_agent/artifacts/audit/

# 看日志内容
Get-Content examples/agent-apps/swe_bio_agent/artifacts/audit/*.jsonl | ConvertFrom-Json
```

## 还能怎么扩展

| 方向 | 你可以加什么 |
|------|-------------|
| 更细的命令白名单 | 在 Guard 里加允许/禁止的模式 |
| 脱敏 | 在 Audit 里给敏感信息打码 |
| 成本追踪 | 记录 token 消耗 |
| 团队通知 | 把审计事件推到 Slack/钉钉 |
| Reviewer 子智能体 | 加一个代码审查约束 |
| 打包分发 | 把你的 creature 做成自己的 defaults 包 |

## 插件长什么样

### Guard 插件骨架

```python
from kohakuterrarium.modules import PluginBase

class RulesGuardPlugin(PluginBase):
    def __init__(self, config):
        super().__init__(config)
        self.rules_read = False
    
    def on_tool_call(self, tool_name, args):
        if tool_name in ['write', 'edit', 'multi_edit']:
            if not self.rules_read:
                return self.block("请先阅读规则文件")
        return self.allow()
    
    def on_event(self, event):
        if event.type == 'rules_read':
            self.rules_read = True
```

### Audit 插件骨架

```python
import json
from pathlib import Path
from datetime import datetime

class AuditLoggerPlugin(PluginBase):
    def __init__(self, config):
        super().__init__(config)
        self.log_path = Path(config.get('log_dir', 'artifacts/audit'))
        self.log_path.mkdir(parents=True, exist_ok=True)
    
    def log(self, event_type, data):
        record = {
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        with open(self.log_path / 'audit.jsonl', 'a') as f:
            f.write(json.dumps(record) + '\n')
```

---

[会话、审计与排错 →](audit-and-sessions)
