# Terrarium

给想让多个 creature 一起配合的人看。

**Terrarium** 就是一层接线。它自己没有 LLM，不负责做判断。它管两件事：一是保存共享 channel，二是管理里面各个 creature 的生命周期。creature 自己并不知道自己待在 terrarium 里；它们只管监听哪些 channel、往哪些 channel 发消息，真正把这些名字接起来的是 terrarium。

先看几个概念：[terrarium](../concepts/multi-agent/terrarium.md)、[root agent](../concepts/multi-agent/root-agent.md)、[channel](../concepts/modules/channel.md)。

Terrarium 现在还算实验性功能。真要拿去跑生产，先看后面的[实话实说](#实话实说)。

## 配置长什么样

```yaml
terrarium:
  name: swe-team
  root:
    base_config: "@kt-biome/creatures/root"
  creatures:
    - name: swe
      base_config: "@kt-biome/creatures/swe"
      channels:
        listen:   [tasks]
        can_send: [review, status]
    - name: reviewer
      base_config: "@kt-biome/creatures/reviewer"
      channels:
        listen:   [review]
        can_send: [status]
  channels:
    tasks:   { type: queue }
    review:  { type: queue }
    status:  { type: broadcast }
```

- **`creatures`**：继承和覆盖规则跟独立 creature 一样，只是每个 creature 还会多出 `channels.listen` 和 `channels.can_send`。
- **`channels`**：支持 `queue`（一条消息只给一个消费者）和 `broadcast`（所有订阅者都能收到）。
- **`root`**：可选。它是 terrarium 外面的用户入口 creature，下面会讲。

channel 也可以写成简写：

```yaml
channels:
  tasks: "work items the team pulls from"
```

字段说明见 [configuration](../reference/configuration.md)。

## 自动创建的 channel

运行时总会自动建这些：

- 每个 creature 一个同名 `queue`，方便别的 creature 直接给它发私信。
- 如果设了 `root`，还会多一个 `report_to_root` queue。

这些都不用自己写。

## channel 怎么接起来

对每个 creature 来说，`listen:` 里每写一个 channel，运行时都会注册一个 `ChannelTrigger`。有消息进来时，它就会触发 controller。系统 prompt 里也会带一小段拓扑说明，告诉 creature 自己在听哪些 channel、又能往哪些 channel 发。

`send_message` 这个 tool 会自动加进去。creature 发消息时，调用它并传 `channel` 和 `content` 就行。默认 bracket 格式长这样：

```
[/send_message]
@@channel=review
@@content=...
[send_message/]
```

如果 creature 用的是 `tool_format: xml` 或 `native`，调用写法会不同，但意思一样。见 [Creatures / Tool format](creatures.md)。

## 运行 terrarium

```bash
kt terrarium run @kt-biome/terrariums/swe_team
```

参数：

- `--mode tui|cli|plain`（默认 `tui`）
- `--seed "Fix the auth bug."`：往 seed channel 塞一条起始消息
- `--seed-channel tasks`：指定 seed 发到哪个 channel
- `--observe tasks review status` / `--no-observe`：是否观察 channel
- `--llm <profile>`：统一覆盖所有 creature 的 LLM
- `--session <path>` / `--no-session`：是否持久化

TUI 模式下，你会看到多标签页：root（如果有）、每个 creature，还有被观察的 channel。CLI 模式下，会把第一个 creature 或 root 挂到 RichCLI 上。

如果只是想看 terrarium 信息，不想直接跑：

```bash
kt terrarium info @kt-biome/terrariums/swe_team
```

## Root agent 模式

root 是一个独立的 creature，只是额外挂了 terrarium 管理工具。它在 terrarium **外面**，从上面管整个 terrarium：

- 自动监听每个 creature 的 channel。
- 接收 `report_to_root`。
- 拿到 terrarium 工具（`terrarium_create`、`terrarium_send`、`creature_start`、`creature_stop` 等）。
- 在 TUI/CLI 模式下充当用户入口。

如果你想让用户只面对一个对话入口，就加 root。要做无界面的协作流程，可以不加。

```yaml
terrarium:
  root:
    base_config: "@kt-biome/creatures/root"
    system_prompt_file: prompts/team_lead.md
```

为什么这么设计，见 [root agent](../concepts/multi-agent/root-agent.md)。

## 运行时热插拔

可以从 root 侧通过工具操作，也可以直接在代码里做：

```python
await runtime.add_creature("tester", tester_agent,
                           listen=["review"], can_send=["status"])
await runtime.add_channel("hotfix", channel_type="queue")
await runtime.wire_channel("swe", "hotfix", direction="listen")
await runtime.remove_creature("tester")
```

root 对应用到的工具是：`creature_start`、`creature_stop`、`terrarium_create`、`terrarium_send`。

热插拔适合临时加专家，不用重启。已有 channel 会接上新的 listener，新 creature 也会在自己的 system prompt 里拿到 channel 拓扑。

## 用 observer 调试

`ChannelObserver` 就是在 channel 上接一个旁路，而且不会破坏原来的消费逻辑。跟 consumer 不一样，observer 读取消息时不会去抢 queue 里的消息。dashboard 底层就是这么干的。代码里可以这样写：

```python
sub = runtime.observer.observe("tasks")
async for msg in sub:
    print(f"[tasks] {msg.sender}: {msg.content}")
```

在 `kt terrarium run` 里加 `--observe`，会给列出的 channel 挂上 observer，并在 TUI 里持续显示这些消息。

## 用代码跑 terrarium

```python
from kohakuterrarium.terrarium.runtime import TerrariumRuntime
from kohakuterrarium.terrarium.config import load_terrarium_config
from kohakuterrarium.core.channel import ChannelMessage

runtime = TerrariumRuntime(load_terrarium_config("@kt-biome/terrariums/swe_team"))
await runtime.start()

tasks = runtime.environment.shared_channels.get("tasks")
await tasks.send(ChannelMessage(sender="user", content="Fix the auth bug."))

await runtime.run()
await runtime.stop()
```

如果你要做流式、多租户，或者长期运行的场景，可以再包一层 `KohakuManager`。见 [以代码方式使用](programmatic-usage.md)。

## 实话实说

terrarium 能不能顺利推进，很看每个 creature 有没有把输出发到对的 channel。模型要是没照做，团队就会卡住。下面这些情况更适合用 terrarium：

- 工作流很明确，channel 拓扑固定，消息格式也比较好猜。
- creature 的 prompt 写得比较扎实，基本会按角色要求来。
- 你需要热插拔或者观察能力。

如果父 creature 自己就能把任务拆开做完，那更适合用 sub-agent，也就是在一个 creature 里做纵向委派。

## 排错

- **团队卡住了，没有消息在动。** 多半是发送方 creature 忘了调用 `send_message`。用 `--observe` 看实时 channel 流量，通常就能定位；很多时候，把发送方 prompt 写得更明确就行。
- **creature 收到 channel 消息却没反应。** 先确认 `listen` 里有这个 channel 名，再检查 `ChannelTrigger` 有没有注册好；`kt terrarium info` 会把 wiring 打出来。
- **root 看不到 creature 在干什么。** root 只能看到它监听的 channel 和 `report_to_root`。把 `report_to_root` 加进相关 creature 的 `can_send` 列表里。
- **creature 一多，启动变慢。** 每个 creature 都会启动自己的 LLM provider 和 trigger manager，所以启动时间大体是线性增长的。

计划中的改进，比如自动路由 round 输出、观察 root 生命周期、动态 terrarium 管理，都记在了 [ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md)。

## 另见

- [Creatures](creatures.md)：terrarium 里的每个条目，本质上都是一个 creature。
- [Composition](composition.md)：如果你只需要一个小循环，不需要完整 terrarium，可以看这个 Python 侧方案。
- [以代码方式使用](programmatic-usage.md)：`TerrariumRuntime` 加 `KohakuManager`。
- [Terrarium 概念说明](../concepts/multi-agent/terrarium.md)：为什么 terrarium 会设计成这样。
