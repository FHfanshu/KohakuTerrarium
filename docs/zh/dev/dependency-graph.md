# 依赖规则

这个项目的 import 只能单向走。平时靠大家自觉，真要查就跑 `scripts/dep_graph.py`。现在运行时没有 import 环，别改着改着又绕回去了。

## 先记住这几句

`utils/` 是最底层，谁都能 import 它，但它不能反过来 import 框架里的东西。`modules/` 只放协议和基类。`core/` 是运行时核心，可以 import `modules/` 和 `utils/`，但**不能** import `builtins/`、`terrarium/`、`bootstrap/`。`bootstrap/` 和 `builtins/` 可以站在 `core/` 上面。`terrarium/` 和 `serving/` 再往上一层。最上面才是 `cli/` 和 `api/`。

## 分层

从底往上看，大概是这样：

```
  cli/, api/                    <- transport 层
  serving/, terrarium/          <- orchestration 层
  bootstrap/, builtins/         <- 装配 + 实现层
  core/                         <- 运行时引擎
  modules/                      <- 协议层（带一点基类）
  parsing/, prompt/, llm/, …    <- 支撑包
  testing/                      <- 依赖整套栈，只给测试用
  utils/                        <- 叶子层
```

各层干的事：

- **`utils/`** — 日志、异步小工具、文件保护。这里不该 import 任何框架代码。真加了，八成是分层放错了。
- **`modules/`** — 协议和基类，比如 `BaseTool`、`BaseOutputModule`、`BaseTrigger`。这里只定义接口，不放具体实现。
- **`core/`** — `Agent`、`Controller`、`Executor`、`Conversation`、`Environment`、`Session`、channel、event、registry，运行时主体都在这。`core/` 不能 import `terrarium/`、`builtins/`、`bootstrap/`、`serving/`、`cli/`、`api/`。一旦这么干，循环依赖很快就回来。
- **`bootstrap/`** — 按配置把 `core/` 组起来，LLM、tools、IO、subagents、triggers 这些都从这里接上。
- **`builtins/`** — 内建 tool、sub-agent、input、output、TUI、user command。像 `tool_catalog`、`subagent_catalog` 这种 catalog 自己也要尽量保持叶子化。
- **`terrarium/`** — 多 agent 运行时。它可以 import `core/`、`bootstrap/`、`builtins/`，反过来不行。
- **`serving/`** — `KohakuManager`、`AgentSession` 这些对外服务包装层。依赖 `core/` 和 `terrarium/`，但不绑死某种传输方式。
- **`cli/`、`api/`** — 最上层入口。一个走 argparse，一个走 FastAPI，都建立在 `serving/` 之上。

源码树里的 ASCII 依赖图在 [`src/kohakuterrarium/README.md`](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/src/kohakuterrarium/README.md)，要对图，以那份为准。

## 为什么要这么分

主要就三件事：

1. **别有环。** 一旦有环，初始化顺序会变得很脆，partial import 和各种 side effect 会一起冒出来。
2. **好测试。** `core/` 不去 import `terrarium/`，测 controller 时就不用把整套多 agent runtime 一起拉起来。
3. **改动范围好判断。** 你改 `utils/`，影响可能很大；你改 `cli/`，一般就只在上层打转。

以前出过这样一条环：
`builtins.tools.registry → terrarium.runtime → core.agent → builtins.tools.registry`

后来是拆出 `tool_catalog` 这种叶子模块，再配合 deferred loader 才解开的。现在还留着两处算合理的 lazy import：`core/__init__.py` 用 `__getattr__` 处理 `core.agent` 的初始化顺序；`terrarium/tool_registration.py` 会把 terrarium tool 的注册拖到第一次查找时再做。

## 检查工具：`scripts/dep_graph.py`

这是个静态 AST 分析器，会扫 `src/kohakuterrarium/` 下所有 `.py`，把 import 边分成三类：

- **runtime** — 顶层 import，模块一加载就会跑。
- **TYPE_CHECKING** — 写在 `if TYPE_CHECKING:` 里，不算进 runtime 图。
- **lazy** — 写在函数体里，也不算进 runtime 图。

只有 runtime 边会拿去查环。

### 命令

```bash
# 概览统计 + 跨组边数量（默认）
python scripts/dep_graph.py

# 检查 runtime SCC cycle
python scripts/dep_graph.py --cycles

# 输出 Graphviz DOT（可接到 `dot -Tsvg`）
python scripts/dep_graph.py --dot > deps.dot

# 用 matplotlib 画 group + module 图，输出到 plans/
python scripts/dep_graph.py --plot

# 上面全跑一遍
python scripts/dep_graph.py --all
```

重点看这些输出：

- **Top fan-out** — import 别人最多的文件，常见是装配代码，比如 `bootstrap/`、`core/agent.py`。
- **Top fan-in** — 被 import 最多的模块，通常是 `utils/`、`modules/base`、`core/events.py`。
- **Cross-group edges** — 跨包边数量。要是突然多出一条 `core/` 指到 `terrarium/` 的边，就得查。
- **SCCs** — 正常应该是空的。只要 Tarjan 算法找出了非平凡 SCC，说明 runtime 图里有环。

`--plot` 会写出 `plans/dep-graph.png` 和 `plans/dep-graph-detailed.png`。大改完之后，把这两张图贴进 PR 里很有用。

### 什么时候跑

- PR 要加新子包之前。
- 你怀疑有循环 import 的时候，比如启动时报 `ImportError`，还提到 partially initialized module。
- 大重构之后，顺手做个检查。

至少跑一下：

```bash
python scripts/dep_graph.py --cycles
```

正常输出应该是：

```
None found. The runtime import graph is acyclic.
```

不是这个结果，就先拆环，再合并。

## 新增 package 往哪放

先想清楚几件事：

- **它是协议，还是运行时逻辑？** 协议放 `modules/`，运行时逻辑放 `core/` 或更上层。
- **它要不要依赖 `core.Agent`？** 要的话，它就不该塞进 `core/` 里。
- **它是内建的，还是扩展？** 内建放 `builtins/`，扩展放独立 package，再用 manifest 接进来。

然后守住这一层自己的 import 规则：

- `utils/` 不能 import 框架代码。
- `modules/` 可以 import `utils/` 和 core typing，别的少碰。
- `core/` 可以 import `modules/`、`utils/`、`llm/`、`parsing/`、`prompt/`。
  不能 import `terrarium/`、`serving/`、`builtins/`、`bootstrap/`。
- `bootstrap/` 和 `builtins/` 可以 import `core/` + `modules/`。
- 其他东西放在这些层之上。

如果你新加的一条边看着就不太对，通常就是真的不对。优先考虑拆一个叶子辅助模块，比如 `tool_catalog`，别第一反应就是往函数里塞 import。函数内 import 不是常规写法，只能当最后手段。

## 另见

- [CLAUDE.md §Import Rules](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/CLAUDE.md) — 这里的规则和那边是一套东西。
- [`src/kohakuterrarium/README.md`](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/src/kohakuterrarium/README.md) — 标准 ASCII 依赖图。
- [internals.md](internals.md) — 按运行流程讲各个子包在干什么。
