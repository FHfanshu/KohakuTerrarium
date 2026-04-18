# Trigger（触发器）

## 它是什么

**Trigger** 是任何不靠用户显式输入、却能唤醒 controller 的东西。定时器、空闲检测器、webhook 接收器、channel 监听器、监控条件，都算 trigger。每个 trigger 都以后台任务运行，在满足触发条件时把 `TriggerEvent` 推到事件队列里。

## 为什么需要它

只靠输入驱动的 agent，只有用户在场时才能工作。现实里的 agent 不是这样。它需要：

- 在没人盯着时继续跑 `/loop` 这种周期性计划；
- 对另一个 creature 发来的 channel 消息作出反应；
- 在最后一个事件过去 N 秒后醒来，做摘要；
- 接收外部服务发来的 webhook；
- 轮询某个资源，在条件变化时触发。

你当然可以把这些都写成临时拼上的代码。这个框架的看法更直接：它们本质上都是一回事，都是事件源，所以应该用同一个抽象。

## 我们怎么定义它

一个 trigger 需要实现：

- 异步生成器 `fire()`，用于产出 `TriggerEvent`；
- `to_resume_dict()` / `from_resume_dict()`，这样 trigger 才能跨 session 持久化和恢复；
- `trigger_id`，用于寻址，这样工具才能列出或取消它。

trigger manager 会为每个已注册的 trigger 启动一个后台任务。每个任务都会循环调用 `fire()`，然后把事件推入队列。

## 我们怎么实现它

内置 trigger 类型有：

- **`timer`** — 每隔 N 秒触发一次，或按 cron 调度触发。
- **`idle`** — 如果 N 秒内没有任何事件，就触发。
- **`channel`** — 监听一个具名 channel；收到消息时触发。
- **`webhook` / `http`** — 接收 POST 请求。
- **`monitor`** — 当作用在 scratchpad / context 上的谓词返回 true 时触发。

`TriggerManager`（`core/trigger_manager.py`）负责管理这些运行中的任务，把完成事件接到 agent 的事件回调上，并把 trigger 状态持久化到 session store，这样 `kt resume` 就能重新创建它们。

配置阶段的 trigger 写在 `config.triggers[]` 里。运行时 trigger 也可以由 agent 自己安装：每个通用 trigger 类（`universal = True` 加 `setup_*` 元数据）都会被包装成独立工具，比如 `add_timer`、`watch_channel`、`add_schedule`。creature 会在 `tools: [{ name: add_timer, type: trigger }]` 下面声明它们。也可以通过 `agent.add_trigger(...)` 以编程方式添加。

## 所以你能做什么

- **周期性 agent。** 每小时触发一次的 `timer`，可以让 creature 定时刷新自己对文件系统或一组指标的视图。
- **跨 creature 连线。** `channel` trigger 是 [terrarium](/concepts/multi-agent/terrarium.md)（英文）真正运转起来的机制。
- **按空闲生成摘要。** 一个在静默两分钟后触发的 `idle`，可以派发 `summarize` sub-agent，再把结果发到日志 channel。
- **接收外部信号。** `webhook` trigger 能让 creature 接收 CI hook、部署事件或上游产品流量。
- **自适应 watcher。** 自定义 trigger 的 `fire()` 可以运行一个小型嵌套 agent，不按固定规则，而是靠判断决定*什么时候*唤醒外层 creature。见 [patterns](/concepts/patterns.md)（英文）。

## 不要被它限制

一个 creature 可以没有 trigger。也可以只有 trigger，没有 input。框架不会给这些配置排高低，只是都支持。还有一点，trigger 本身也是 Python 对象，所以你可以把一个 agent 放进 trigger 里：让 watcher 先“想一想”要不要触发，而不是照着手写规则执行。这样的模式让“agent 式环境行为”更容易搭起来。

## 另见

- [Input](/concepts/modules/input.md)（英文）— 用户内容这个特例 trigger。
- [Channel](/concepts/modules/channel.md)（英文）— 支撑多智能体通信的 trigger 类型。
- [reference/builtins.md — Triggers](/reference/builtins.md)（英文）— 完整清单。
- [patterns.md — adaptive watcher](/concepts/patterns.md)（英文）— trigger 里嵌 agent。
