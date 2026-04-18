# 配置文件写法

creature 就是一个目录，里面有个 `config.yaml`，再加些 prompt 文件和插件脚本。

## 最小结构

```text
my-creature/
  config.yaml        # 主配置
  prompts/
    system.md        # 系统提示词
  custom/
    ...              # 自定义插件
```

## config.yaml 长什么样

下面是一个本地扩展示例 creature 的真实配置：

```yaml
name: swe_bio_agent
version: "1.0"
base_config: "@kt-defaults/creatures/swe"

system_prompt_file: prompts/system.md
session_key: swe_bio_agent

input:
  type: cli
  prompt: "> "

output:
  type: stdout
  controller_direct: true

plugins:
  - name: rules_guard
    type: custom
    module: ./custom/guard_plugin.py
    class: RulesGuardPlugin
  - name: audit_logger
    type: custom
    module: ./custom/audit_plugin.py
    class: AuditLoggerPlugin
```

> 这个 `swe_bio_agent` 是本地扩展示例，不是官方远端仓库当前默认自带内容。
> 真正稳定可直接引用的基座是 `@kt-defaults/creatures/swe`。

别被吓到，下面逐个讲。

## `name`

就是智能体的名字，用在 session 命名和日志里。取个清楚的名字就行。

## `base_config`

**这个字段最实用。** 填了它，你就不需要把默认 `swe` 的配置抄一遍了。

```yaml
base_config: "@kt-defaults/creatures/swe"
```

意思是：先加载默认 `swe` 的全部配置，再把你自己的覆盖上去。工具、子智能体、prompt layering 这些全都继承了。

> 新手最容易犯的错：不用 `base_config`，把默认配置整个复制一遍然后改。这样默认 `swe` 升级了你就收不到了。

## `system_prompt_file`

指定你自己的提示词文件。

**好的写法**：只放这些内容——
- 角色定位
- 方法论
- 安全规则
- 项目规则读取要求

**别写这些**：完整的工具说明。框架会自动注入工具列表，你写了就是重复，只会让 prompt 臃肿。

## `input` / `output`

控制交互方式。

输入类型：

| type | 说明 |
|------|------|
| `cli` | 标准命令行 |
| `tui` | 全屏终端 |
| `none` | 不接收输入，纯触发式 |
| `custom` | 自己写 |

输出类型：

| type | 说明 |
|------|------|
| `stdout` | 直接输出 |
| `tui` | 全屏终端 |
| `custom` | 自己写 |

示例：

```yaml
input:
  type: cli
  prompt: "> "

output:
  type: stdout
  controller_direct: true
```

## `plugins`

**最重要的扩展点。** 通过插件你可以拦截工具调用、记录日志、加限制。

```yaml
plugins:
  - name: rules_guard
    type: custom
    module: ./custom/guard_plugin.py
    class: RulesGuardPlugin
    options:
      modify_tools:
        - write
        - edit
        - multi_edit
```

每个字段的意思：

| 字段 | 说明 |
|------|------|
| `name` | 插件实例的名字，要唯一 |
| `type` | `custom` = 从本地目录加载 |
| `module` | 相对 creature 根目录的 `.py` 文件路径 |
| `class` | 要实例化的类名 |
| `options` | 传给插件构造函数的参数 |

## 其他配置块

### `controller` — 控制模型和推理行为

```yaml
controller:
  llm: gpt-5.4
  reasoning_effort: medium
  tool_format: native
```

### `tools` — 指定可用工具

从零写 creature 时需要显式列出：

```yaml
tools:
  - read
  - write
  - edit
  - bash
  - grep
  - glob
```

用了 `base_config` 的话，工具是继承来的，不用再写。

### `subagents` — 子智能体

```yaml
subagents:
  - name: worker
    type: worker
    config: ./subagents/worker.yaml
```

### `compact` — 上下文压缩

会话太长时自动压缩，避免 token 爆掉：

```yaml
compact:
  enabled: true
  threshold: 100000
  mode: semantic
```

### `termination` — 终止条件

```yaml
termination:
  max_turns: 100
  max_time: 3600
```

## 最容易踩的坑

| 问题 | 原因 | 怎么修 |
|------|------|--------|
| `@kt-defaults/... not found` | 没装 kt-defaults | 跑 `kt install https://github.com/Kohaku-Lab/kt-defaults.git` |
| prompt 又长又臭 | 手抄了工具说明 | 只写角色规则，工具说明框架自动注入 |
| 配置又多又乱 | 没用 `base_config` | 继承默认 creature，只写增量部分 |
| 模型老是乱来 | 只靠插件拦截，没在 prompt 里说规矩 | prompt 和 plugin 要双管齐下 |

## 检查配置对不对

```powershell
kt info my-creature/
```

配对了会显示：

```
Name: my_creature
Valid: true
Base: @kt-defaults/creatures/swe
Tools: 25 (+0 custom)
Subagents: 5
Plugins: 2
```

配错了会告诉你哪里有问题：

```
Name: my_creature
Valid: false
Errors:
  - plugins[0].module: file not found: ./custom/missing.py
```

---

[定制 SWE 智能体 →](swe-bio-agent)
