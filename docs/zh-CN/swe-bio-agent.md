# 定制 SWE 智能体



这篇对应的示例代码是：`examples/agent-apps/swe_bio_agent`

先说明一下：它是一个**本地扩展示例**，不是官方远端仓库当前默认自带的 creature。

- 如果你的工作区里有这个目录，这篇可以直接照着操作
- 如果没有这个目录，这篇也可以当作“如何基于默认 `@kt-biome/creatures/swe` 做增强版”的参考

它不用于替代默认 `swe`，而是在默认 `swe` 之上补两类能力：

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
    humanizer_docs.py   # 文档润色子智能体
  artifacts/
    audit/              # 日志输出目录
```

## 它是怎么设计的

### 1. 继承默认 `swe`

```yaml
base_config: "@kt-biome/creatures/swe"
```

这样做有几个直接的好处：

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

prompt 只能起到“引导”作用，模型不一定总会照做。真正负责硬拦截的是 `custom/guard_plugin.py`：

| 什么时候 | 拦什么 |
|----------|--------|
| 规则没读完 | `write`、`edit`、`multi_edit` |
| 规则没读完 | `worker` 子智能体 |
| 总是 | `git reset --hard`、`git clean -fd`、`rm -rf` |

设计思路可以概括成八个字：**prompt 引导，plugin 硬拦**。两层一起用，会比只写 prompt 稳得多。

### 4. 加一个文档润色子智能体

这个示例还额外挂了一个 `humanizer_docs` 子智能体。

它适合做这类任务：

- 先读代码库和文档，弄清楚真实行为
- 再把 README、教程、说明文档改得更自然、更像人写的
- 去掉机械感、宣传腔和明显的 AI 写作痕迹
- 但不乱改事实，不凭空补功能

它主要围绕文档工作，常用这些工具：

- `read`
- `glob`
- `grep`
- `tree`
- `think`
- `write`
- `edit`
- `multi_edit`

可以把它理解成：**专门处理文档探索与润色的子智能体，会改文档，但不参与代码实现。**

### 5. 用 Audit 插件记日志

`custom/audit_plugin.py` 把这些信息写进 JSONL：

| 事件 | 记什么 |
|------|--------|
| `agent_start` | 启动时间、session id、工作目录 |
| `rules_found` | 发现了哪些规则文件 |
| `user_input` | 用户输的什么 |
| `tool_start/end` | 工具调用参数和结果 |
| `rules_read` | 规则文件读完了 |
| `subagent_start/end` | 子智能体调用和返回（包括 `humanizer_docs`） |
| `agent_stop` | 结束时间 |

## 怎么运行

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

如果你手头没有这份本地扩展示例，就先运行默认 SWE：

```powershell
kt run @kt-biome/creatures/swe --mode cli
```

## 跑完后怎么看

```powershell
# 看有没有 session 文件
dir ~/.kohakuterrarium/sessions/*.kohakutr

# 看审计日志
dir examples/agent-apps/swe_bio_agent/artifacts/audit/

# 看日志内容
Get-Content examples/agent-apps/swe_bio_agent/artifacts/audit/*.jsonl | ConvertFrom-Json
```

## 还能怎么扩展

| 方向 | 可以继续加什么 |
|------|----------------|
| 更细的命令白名单 | 在 Guard 里补充允许/禁止模式 |
| 脱敏 | 在 Audit 里对敏感信息打码 |
| 成本追踪 | 记录 token 消耗 |
| 团队通知 | 把审计事件推到 Slack/钉钉 |
| Reviewer 子智能体 | 增加代码审查约束 |
| 文档工作流 | 继续细分成术语统一、教程改写、发布说明润色等子智能体 |
| 打包分发 | 把自己的 creature 做成 defaults 包 |

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
