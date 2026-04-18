# 依赖规则

这个包的 import 方向是严格单向的。规则靠约定执行，也会用 `scripts/dep_graph.py` 校验。当前运行时没有循环依赖，别把它弄回去。

## 一段话讲清规则

`utils/` 是叶子层。所有地方都可以 import 它，但它自己不能反向 import 框架里的东西。`modules/` 只放协议定义。`core/` 是运行时，能 import `modules/` 和 `utils/`，但**绝不能** import `builtins/`、`terrarium/` 或 `bootstrap/`。`bootstrap/` 和 `builtins/` 可以 import `core/` + `modules/`。`terrarium/` 和 `serving/` 站在更上层，依赖 `core/` + `bootstrap/`。`cli/` 和 `api/` 则位于最上层，依赖 `serving/` + `terrarium/`。

## 分层

从最底层叶子到最上层传输层：

```
  cli/, api/                    <- transport
  serving/, terrarium/          <- orchestration
  bootstrap/, builtins/         <- assembly + implementations
  core/                         <- runtime engine
  modules/                      <- protocols（以及少量基类）
  parsing/, prompt/, llm/, …    <- support packages
  testing/                      <- 依赖整个栈，仅供测试使用
  utils/                        <- leaf
```

逐层说明：

- **`utils/`** —— 日志、异步辅助、文件保护。这里不能 import 任何框架内部包。只要往这里加框架依赖，基本就是错的。
- **`modules/`** —— 协议和基类定义。比如 `BaseTool`、`BaseOutputModule`、`BaseTrigger`。这里不放实现，方便上层都能依赖它。
- **`core/`** —— `Agent`、`Controller`、`Executor`、`Conversation`、`Environment`、`Session`、channels、events、registry。这里才是运行时本体。`core/` 绝不能 import `terrarium/`、`builtins/`、`bootstrap/`、`serving/`、`cli/` 或 `api/`，否则循环依赖会重新出现。
- **`bootstrap/`** —— 工厂函数层，把配置装配成 `core/` 组件（LLM、tools、IO、subagents、triggers）。会 import `core/` 和 `builtins/`。
- **`builtins/`** —— 各种内置 tool、sub-agent、input、output、TUI、user command。内部目录如 `tool_catalog`、`subagent_catalog` 属于叶子模块，用 deferred loader 延迟装载。
- **`terrarium/`** —— 多智能体运行时。依赖 `core/`、`bootstrap/`、`builtins/`。这些层都不该反向依赖它。
- **`serving/`** —— `KohakuManager`、`AgentSession`。依赖 `core/` 和 `terrarium/`，但不关心具体传输协议。
- **`cli/`、`api/`** —— 最上层。一个是 argparse 入口，一个是 FastAPI 应用，二者都消费 `serving/`。

可把 [`src/kohakuterrarium/README.md`](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/src/kohakuterrarium/README.md)（英文）里的 ASCII 依赖图当成权威版本。

## 为什么要这样分

主要是三个目的：

1. **没有环。** 循环依赖会带来初始化顺序脆弱、partial import 报错，以及启动期副作用。
2. **方便测试。** 只要 `core/` 不 import `terrarium/`，就能单测 controller，而不用把多智能体运行时整个拉起来。只要 `modules/` 只放协议，实现就能随时替换。
3. **改动范围清晰。** 改 `utils/`，影响面最大；改 `cli/`，几乎不会向下波及。分层之后，影响范围是可预期的。

历史上曾经有一条循环链：
`builtins.tools.registry → terrarium.runtime → core.agent → builtins.tools.registry`。
后来通过引入 `tool_catalog` 这个叶子模块，再配合 deferred loader，把这条环拆掉了。细节可以去翻 git 历史里 [`internals.md`](/dev/internals.md)（英文）的 legacy notes。现在只有两处延迟 import 是被允许的：`core/__init__.py` 用 `__getattr__` 避开 `core.agent` 的初始化顺序问题；`terrarium/tool_registration.py` 会把 terrarium tool 的注册延后到第一次查找时。

## 工具：`scripts/dep_graph.py`

这是个静态 AST 分析器。它会遍历 `src/kohakuterrarium/` 下的所有 `.py` 文件，解析 `import` / `from ... import`，并把每条边分成三类：

- **runtime** —— 顶层 import，模块加载时就会执行
- **TYPE_CHECKING** —— 放在 `if TYPE_CHECKING:` 里，不计入运行时依赖图
- **lazy** —— 写在函数体内部的 import，不计入运行时依赖图

只有 runtime 边会参与循环检测。

### 命令

```bash
# 摘要统计 + 跨分组依赖计数（默认）
python scripts/dep_graph.py

# 检查 runtime SCC 循环
python scripts/dep_graph.py --cycles

# 输出 Graphviz DOT（可接 `dot -Tsvg`）
python scripts/dep_graph.py --dot > deps.dot

# 用 matplotlib 把分组图和模块图渲染到 plans/
python scripts/dep_graph.py --plot

# 上面全部都做
python scripts/dep_graph.py --all
```

关键输出包括：

- **Top fan-out** —— import 别人的模块最多的是谁。通常是装配代码，比如 `bootstrap/`、`core/agent.py`。
- **Top fan-in** —— 被 import 次数最多的是谁。一般会看到 `utils/`、`modules/base`、`core/events.py` 靠前。
- **Cross-group edges** —— 跨包边数量，类似条形图。如果突然出现 `core/` 指向 `terrarium/` 的新边，就该查。
- **SCCs** —— 理想状态下一直为空。只要 Tarjan 算法找到了非平凡 SCC，运行时依赖图里就有环。

`--plot` 会写出 `plans/dep-graph.png`（分组级、环形布局）和 `plans/dep-graph-detailed.png`（模块级、同心圆布局）。做大重构时，这两张图很适合放到 PR 里辅助审查。

### 什么时候跑

- 提交一个新增子包的 PR 之前
- 怀疑有循环 import 时（典型症状是启动时报 `ImportError`，提示 partially initialized module）
- 做完大规模重构之后，拿来做一次 sanity check

跑 `python scripts/dep_graph.py --cycles`，确认输出是：

```text
None found. The runtime import graph is acyclic.
```

如果不是，就先把环拆掉，再谈合并。

## 新增包时怎么放

先选对层级，问自己几个问题：

- **它有运行时行为，还是只放基类 / 协议？** 只放协议就进 `modules/`；有运行时行为，就放 `core/` 或更高层的专用子包。
- **它需不需要 `core.Agent`？** 如果需要，它就在 `core/` 上层，不该塞进 `core/` 里面。
- **它是 KT 自带能力，还是扩展包？** 内置功能进 `builtins/`；扩展功能应放在独立包里，通过 package manifest 接入。

选好层之后，继续遵守这层的 import 规则：

- `utils/` 不 import 框架内部任何东西。
- `modules/` 只 import `utils/` 和核心类型定义，不要再往上。
- `core/` 只能 import `modules/`、`utils/`、`llm/`、`parsing/`、`prompt/`。
  绝不能 import `terrarium/`、`serving/`、`builtins/`、`bootstrap/`。
- `bootstrap/` 和 `builtins/` 可以 import `core/` + `modules/`。
- 其他所有层都放在它们之上。

如果一条新依赖边看起来很别扭，通常说明它本来就不该存在。优先引入一个叶子辅助模块（比如 `tool_catalog`）来拆环，而不是先拿函数内 import 糊过去。函数内 import 在 [CLAUDE.md §Import Rules](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/CLAUDE.md)（英文）里本来就被视为最后手段，不是常规方案。

## 另见

- [CLAUDE.md §Import Rules](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/CLAUDE.md)（英文）—— 这些约束对应的代码规范
- [`src/kohakuterrarium/README.md`](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/src/kohakuterrarium/README.md)（英文）—— 权威 ASCII 依赖图
- [internals.md](/dev/internals.md)（英文）—— 逐段说明每个子包的职责
