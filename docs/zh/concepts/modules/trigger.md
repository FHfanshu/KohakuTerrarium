# Trigger

## 它是什么

**trigger** 是一切不用显式用户输入、也能把 controller 叫醒的东西。timer、idle detector、webhook receiver、channel listener、monitor condition，都算 trigger。每个 trigger 都作为后台 task 运行；一旦满足触发条件，就往事件队列里推 `TriggerEvent`。

## 为什么要有它

一个只靠 input 驱动的 agent，只有用户在旁边时才能工作。但真 agent 往往需要：

- 没人盯着时也能跑 `/loop` 这类周期性计划；
- 收到另一个 creature 的 channel 消息就醒；
- 在最后一个事件过去 N 秒后醒来做总结；
- 接外部服务打来的 webhook；
- 轮询某个资源，等条件翻转时触发。

你当然可以把这些全都各写一套特判代码。但框架的看法更干脆：它们本质上都是事件源，应该共享一层抽象。

## 怎么定义它

一个 trigger 会实现：

- 异步生成器 `fire()`，不断 yield `TriggerEvent`
- `to_resume_dict()` / `from_resume_dict()`，这样 trigger 才能跨 session 保存和恢复
- 一个 `trigger_id`，方便按地址列出或取消

trigger manager 会给每个已注册 trigger 起一个后台 task。每个 task 都循环调用 `fire()`，再把产出的事件推进去。

## 怎么实现它

内置 trigger 类型包括：

- **`timer`** —— 每 N 秒触发一次，或者按 cron schedule 触发。
- **`idle`** —— 如果连续 N 秒没有任何事件，就触发。
- **`channel`** —— 监听某个具名 channel；一有消息就触发。
- **`webhook` / `http`** —— 接收 POST 请求。
- **`monitor`** —— 当某个针对 scratchpad / context 的谓词变成 true 时触发。

接收侧常见的 `TriggerEvent` 类型还包括：`user_input`（来自 input 模块）、`timer`、`channel_message`（来自 channel trigger）、`tool_complete`、`subagent_output`、`creature_output`（另一个 creature 通过 `output_wiring` 在回合结束自动送来的输出——这是框架发的，不是某个模块自己触发的），以及 `error`。

`TriggerManager`（`core/trigger_manager.py`）负责这些运行中的 task，把完成事件接回 agent 的事件回调里，并把 trigger 状态持久化到 session store，这样 `kt resume` 才能把它们重新建起来。

配置期 trigger 写在 `config.triggers[]` 里。运行时 trigger 也可以由 agent 自己安装——每个通用 trigger 类（`universal = True` 并带 `setup_*` 元数据）都会被包成自己的 tool，比如 `add_timer`、`watch_channel`、`add_schedule`。只要 creature 在 `tools: [{ name: add_timer, type: trigger }]` 里列出来，LLM 就能自己装。程序里也可以直接 `agent.add_trigger(...)`。

## 你能拿它做什么

- **周期性 agent。** 配一个每小时触发的 `timer`，让 creature 定时刷新文件系统视图或一组指标。
- **跨 creature 连线。** `channel` trigger 是基于 channel 的 terrarium 通信关键机制。对于那种确定性的流水线边，框架还会在 creature 声明了 `output_wiring` 时，于回合结束自动发出 `creature_output` 事件；见 [terrarium](/zh/concepts/multi-agent/terrarium.md)。
- **空闲后总结。** 配一个两分钟静默后触发的 `idle`，让它去调 `summarize` sub-agent，再把结果发到日志 channel。
- **接外部信号。** `webhook` trigger 能把 creature 变成 CI hook、部署事件或上游产品流量的接收端。
- **自适应 watcher。** 你可以写一个自定义 trigger，让它的 `fire()` 里再跑一个小 nested agent，由判断来决定**什么时候**唤醒外层 creature，而不是硬编码规则。见 [patterns](/zh/concepts/patterns.md)。

## 别把它看得太死

creature 可以一个 trigger 都没有。也可以只有 trigger，没有 input。框架不偏袒哪种配置，反正都支持。而且因为 trigger 本身也是 Python 对象，你完全可以把 agent 塞进去——让 watcher 先“想一想”，再决定要不要触发，而不是照着固定规则走。这也是 agentic ambient behaviour 比较便宜就能搭出来的原因。

## 另见

- [Input](/zh/concepts/modules/input.md) —— 面向用户内容的那个特殊 trigger。
- [Channel](/zh/concepts/modules/channel.md) —— 支撑 multi-agent 通信的 trigger 类型。
- [reference/builtins.md — Triggers](/zh/reference/builtins.md) —— 完整列表。
- [patterns.md — adaptive watcher](/zh/concepts/patterns.md) —— trigger 里套 agent 的做法。