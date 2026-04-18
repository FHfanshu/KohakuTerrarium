# Terrariums

给需要让多个 creature 协作的人看。

**Terrarium** 本质上就是一层连线：自己没有 LLM，也不做决策。它负责持有共享 channel，并管理里面那些 creature 的生命周期。creature 不会知道自己在 terrarium 里；它们只管监听 channel 名、往 channel 名发消息，真正把这些名字接起来的是 terrarium。

概念预读：[terrarium](/concepts/multi-agent/terrarium.md)（英文）、[root agent](/concepts/multi-agent/root-agent.md)（英文）、[channel](/concepts/modules/channel.md)（英文）。

Terrarium 现在还属于实验性功能。要拿去做面向生产的东西，先看下面的[实话实说](/guides/terrariums.md#the-honest-bit)（英文）。

## 配置结构

```yaml
terrarium:
  name: swe-team
  root:
    base_config: "@kt-defaults/creatures/root"
  creatures:
    - name: swe
      base_config: "@kt-defaults/creatures/swe"
      channels:
        listen:   [tasks]
        can_send: [review, status]
    - name: reviewer
      base_config: "@kt-defaults/creatures/reviewer"
      channels:
        listen:   [review]
        can_send: [status]
  channels:
    tasks:   { type: queue }
    review:  { type: queue }
    status:  { type: broadcast }
```

- **`creatures`** —— 继承和覆盖规则和独立 creature 一样，只是每个 creature 还会多出 `channels.listen` / `channels.can_send`。
- **`channels`** —— 可选 `queue`（每条消息只会被一个 consumer 取走）或 `broadcast`（每个 subscriber 都能收到每条消息）。
- **`root`** —— 可选。它是 terrarium 外面的用户入口 creature，下面会讲。

channel 描述也可以写成简写：

```yaml
channels:
  tasks: "work items the team pulls from"
```

字段说明见 [reference/configuration](/reference/configuration.md)（英文）。

## 自动创建的 channel

运行时总会创建这些 channel：

- 每个 creature 都有一个同名 `queue`，方便其他 creature 给它发私信。
- 如果设置了 `root`，还会有一个 `report_to_root` queue。

这些都不用自己声明。

## channel 是怎么连起来的

对每个 creature 来说，`listen:` 里每出现一个条目，运行时就会注册一个 `ChannelTrigger`。消息一到，它就触发 controller。系统 prompt 里还会带一小段拓扑说明，告诉这个 creature 它在监听哪些 channel、又能往哪些 channel 发送。

`send_message` tool 会自动加进去。creature 发消息时，调用这个 tool，并传 `channel` 和 `content` 参数就行。默认的 bracket 格式长这样：

```
[/send_message]
@@channel=review
@@content=...
[send_message/]
```

如果你的 creature 用的是 `tool_format: xml` 或 `native`，调用写法会不一样，但语义不变。见 [Creatures — Tool format](/guides/creatures.md)（英文）。

## 运行 terrarium

```bash
kt terrarium run @kt-defaults/terrariums/swe_team
```

参数：

- `--mode tui|cli|plain`（默认 `tui`）
- `--seed "Fix the auth bug."` —— 往 seed channel 注入一条起始消息
- `--seed-channel tasks` —— 覆盖接收 seed 的 channel
- `--observe tasks review status` / `--no-observe` —— 是否观察 channel
- `--llm <profile>` —— 覆盖所有 creature 使用的 LLM
- `--session <path>` / `--no-session` —— 是否持久化

在 TUI 模式下，你会看到多标签页视图：root（如果有）、每个 creature，以及被观察的 channel。CLI 模式下，会把第一个 creature（或者 root）挂到 RichCLI 上。

如果只想看 terrarium 信息，不运行它：

```bash
kt terrarium info @kt-defaults/terrariums/swe_team
```

## Root agent 模式

root 是一个独立的 creature，只是额外挂了 terrarium 管理工具。它在 terrarium **外面**，从更高一层驱动整个 terrarium：

- 自动监听每个 creature 的 channel。
- 接收 `report_to_root`。
- 拿到 terrarium 工具（`terrarium_create`、`terrarium_send`、`creature_start`、`creature_stop` 等）。
- 在 TUI/CLI 模式下，作为面向用户的交互入口。

如果你想把交互入口收敛成一个对话面，就用 root。要做无界面的协作流程，就可以不加。

```yaml
terrarium:
  root:
    base_config: "@kt-defaults/creatures/root"
    system_prompt_file: prompts/team_lead.md
```

设计原因见 [concepts/multi-agent/root-agent](/concepts/multi-agent/root-agent.md)（英文）。

## 运行时热插拔

可以从 root 侧通过工具操作，也可以直接在代码里做：

```python
await runtime.add_creature("tester", tester_agent,
                           listen=["review"], can_send=["status"])
await runtime.add_channel("hotfix", channel_type="queue")
await runtime.wire_channel("swe", "hotfix", direction="listen")
await runtime.remove_creature("tester")
```

root 用到的对应工具是：`creature_start`、`creature_stop`、`terrarium_create`、`terrarium_send`。

热插拔适合临时加一些 specialist，而且不用重启。已有 channel 会接上新的 listener；新 creature 也会在自己的 system prompt 里拿到 channel 拓扑信息。

## 用 observer 做调试

`ChannelObserver` 是挂在 channel 上的非破坏性旁路。和 consumer 不一样，observer 读取消息时不会去竞争 queue 里的消息。dashboard 底层就是这么做的。代码里可以这样用：

```python
sub = runtime.observer.observe("tasks")
async for msg in sub:
    print(f"[tasks] {msg.sender}: {msg.content}")
```

在 `kt terrarium run` 里加 `--observe`，会给列出的 channel 挂上 observer，并在 TUI 里持续显示这些消息。

## 以编程方式使用 terrarium

```python
from kohakuterrarium.terrarium.runtime import TerrariumRuntime
from kohakuterrarium.terrarium.config import load_terrarium_config
from kohakuterrarium.core.channel import ChannelMessage

runtime = TerrariumRuntime(load_terrarium_config("@kt-defaults/terrariums/swe_team"))
await runtime.start()

tasks = runtime.environment.shared_channels.get("tasks")
await tasks.send(ChannelMessage(sender="user", content="Fix the auth bug."))

await runtime.run()
await runtime.stop()
```

如果你要做 streaming、多租户，或者长期运行的场景，外面再包一层 `KohakuManager`。见 [Programmatic Usage](/guides/programmatic-usage.md)（英文）。

## 实话实说

terrarium 能不能推进下去，取决于每个 creature 是否把输出发到了对的 channel。模型一旦没照做，整个团队就会卡住。下面这些情况更适合用 terrarium：

- 工作流很明确（channel 拓扑固定，消息格式也比较可预测）。
- creature 的 prompt 写得够好，而且基本会按角色说明办事。
- 你需要热插拔或者观察能力。

如果父 creature 自己就能完成任务拆解，更适合用 sub-agent（也就是在一个 creature 内做纵向委派）。

## 故障排查

- **团队卡住了，没有消息在流动。** 很可能是发送方 creature 忘了调用 `send_message`。可以用 `--observe` 直接看 channel 流量；多数时候，把发送方的 prompt 写得更硬一点就能解决。
- **creature 对 channel 消息没反应。** 先确认 `listen` 里有这个 channel 名，另外检查 `ChannelTrigger` 是否已经注册好（`kt terrarium info` 会打印 wiring）。
- **root 看不到 creature 在做什么。** root 只能看到它监听的 channel 和 `report_to_root`。把 `report_to_root` 加进相关 creature 的 `can_send` 列表里。
- **creature 一多，启动就很慢。** 每个 creature 都会启动自己的 LLM provider 和 trigger manager，所以启动时间大致会线性增长。

计划中的改进（自动路由 round 输出、root 生命周期观察、动态 terrarium 管理）记录在 [ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md)（英文）。

## 另见

- [Creatures](/guides/creatures.md)（英文）—— terrarium 里的每个条目本质上都是一个 creature。
- [Composition](/guides/composition.md)（英文）—— 如果你只需要一个小循环，不需要完整 terrarium，可以用这个 Python 侧方案。
- [Programmatic Usage](/guides/programmatic-usage.md)（英文）—— `TerrariumRuntime` + `KohakuManager`。
- [Concepts / terrarium](/concepts/multi-agent/terrarium.md)（英文）—— terrarium 为什么会设计成这样。
