# Terrarium

给想让多个 creature 一起配合的人看。

**Terrarium** 就是一层接线。它自己没有 LLM，不负责做判断。它管三件事：一是保存共享 channel，二是管理里面各个 creature 的生命周期，三是提供框架层的**输出路由**——让某个 creature 一轮结束后的输出，自动送到指定目标。creature 自己并不知道自己待在 terrarium 里；它们只管监听哪些 channel、往哪些 channel 发消息，或者声明自己的回合结束输出该自动流向谁，真正把这些名字接起来的是 terrarium。

先看几个概念：[terrarium](./concepts/multi-agent/terrarium.md)、[root agent](./concepts/multi-agent/root-agent.md)、[channel](./concepts/modules/channel.md)。

我们现在把 terrarium 看成一种**横向多智能体的候选架构**：输出路由 + channel + 热插拔 + 观察 + root 生命周期信号，这套组合今天已经能用，kt-biome 里的四个 terrarium 也都在完整验证它。至于“具体什么场景该怎么搭才最顺手”，我们还在继续摸索；见后面的[现在的定位，实话实说](#现在的定位实话实说)和 [ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md)。

## 配置长什么样

```yaml
terrarium:
  name: swe-team
  root:
    base_config: "@kt-biome/creatures/general"
    system_prompt_file: prompts/root.md    # 这个团队专用的委派 prompt，跟 terrarium 放一起
  creatures:
    - name: swe
      base_config: "@kt-biome/creatures/swe"
      output_wiring: [reviewer]            # 确定性边：每次 swe 回合结束都送 reviewer
      channels:
        listen:   [tasks, feedback]
        can_send: [status]
    - name: reviewer
      base_config: "@kt-biome/creatures/swe"
      system_prompt_file: prompts/reviewer.md   # reviewer 角色用 prompt 表达，不一定要单独的 creature
      channels:
        listen:   [status]
        can_send: [feedback, results, status]   # 条件分支：通过 -> results，打回 -> feedback
  channels:
    tasks:    { type: queue }
    feedback: { type: queue }
    results:  { type: queue }
    status:   { type: broadcast }
```

- **`creatures`**：继承和覆盖规则跟独立 creature 一样，只是每个 creature 还会多出 `channels.listen`、`channels.can_send`，以及可选的 `output_wiring`。
- **`channels`**：支持 `queue`（一条消息只给一个消费者）和 `broadcast`（所有订阅者都能收到）。
- **`output_wiring`**：按 creature 配置一组目标，让这个 creature 的回合结束输出自动送过去。下面单独讲。
- **`root`**：可选。它是 terrarium 外面的用户入口 creature，下面会讲。kt-biome 不提供通用 `root` creature；每个 terrarium 自己带自己的 `prompts/root.md`。

channel 也可以写成简写：

```yaml
channels:
  tasks: "work items the team pulls from"
```

字段说明见 [configuration](./reference/configuration.md)。

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
- 自动收到一段生成出来的“terrarium 感知”prompt，知道团队里有哪些 creatures 和 channels。
- 在 TUI/CLI 模式下充当用户入口。

如果你想让用户只面对一个对话入口，就加 root。要做无界面的协作流程，可以不加。

```yaml
terrarium:
  root:
    base_config: "@kt-biome/creatures/general"
    system_prompt_file: prompts/root.md   # 这个团队专用的委派 prompt
```

kt-biome 不提供一个通用 `root` creature。每个 terrarium 自己定义自己的 `root:` 和旁边那份 `prompts/root.md`——这样 prompt 可以直接写真实团队成员名，比如“写代码就交给 `driver`”。管理工具集和拓扑认知则由框架自动补上。

为什么这么设计，见 [root agent](./concepts/multi-agent/root-agent.md)。

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

## 输出路由

channel 依赖 creature 自己记得调用 `send_message`。但如果某条边本来就是确定性的——比如“coder 每次写完，runner 都应该立刻跑它写出来的内容”——框架还提供另一种方式：**输出路由**。

creature 可以在配置里声明，自己的回合结束输出该自动发给谁。每到回合边界，框架都会往每个目标的事件队列里塞一个 `creature_output` `TriggerEvent`。不需要 `send_message`，不需要 `ChannelTrigger`，中间也不需要 channel。

```yaml
# terrarium.yaml 里的 creature 条目
- name: coder
  base_config: "@kt-biome/creatures/swe"
  output_wiring:
    - runner                              # 简写 = {to: runner, with_content: true}
    - { to: root, with_content: false }   # 生命周期 ping（只带元数据）
  channels:
    listen: [reverts, team_chat]
    can_send: [team_chat]
```

完整字段见 [configuration 参考里的输出路由](./reference/configuration.md#输出路由)。先抓住几个关键点：

- **`to: <creature-name>`**：指向同一个 terrarium 里的另一个 creature。
- **`to: root`**：这是个特殊值，指向 terrarium 外面的 root agent。很适合做生命周期 ping；哪怕 root 没有在听某个 channel，也能收到这个事件。
- **`with_content: false`**：事件里的 `content` 会留空，只表示“这一轮结束了”，不带正文。
- **`prompt` / `prompt_format`**：可以自定义接收方看到的 prompt override 文本。

### 什么时候用输出路由，什么时候继续用 channel

优先用 **输出路由**，如果：

- 这条边是确定性的——一个 creature 每轮输出都必须流向下一个阶段。
- 你想看生命周期信号，但不想依赖 creature 主动 `send_message`。
- 流程是线性的，或者虽然会回环，但回环本身也是无条件发生的。

继续用 **channel**，如果：

- 这条边是条件式的。reviewer 要决定通过还是打回；analyzer 要决定保留还是丢弃。输出路由不会分支，channel 可以。
- 这是广播、状态流、团队群聊——消息可以被很多人看，也不是每个人都必须处理。
- 你想要“谁都能说，谁都能听”的群聊形状。

一个 terrarium 里两种机制完全可以混用。kt-biome 的 `auto_research` 就是用输出路由串起那些棘轮式边（ideator → coder → runner → analyzer），再用 channel 处理 analyzer 的保留/丢弃分支和团队状态广播。

### 接收方眼里，输出路由事件长什么样

这个事件会直接落进目标 creature 的事件队列，走的还是普通 trigger 的 `_process_event` 路径。所以在 TUI 里你看到的照样是一次正常回合：prompt 注入、LLM 输出、tool 调用，全都照旧。挂在接收方上的 plugin 也会像处理别的事件一样，在现有的 `on_event` hook 里看到它；不需要新的 plugin API。

## 现在的定位，实话实说


现在已经有两种协作机制，足够覆盖大多数团队形状：channel（tool + trigger，发送方自愿发送）和输出路由（框架级、自动发生）。kt-biome 的 terrarium 也已经在两边都跑通：确定性流水线边用输出路由，条件分支和群聊/状态流用 channel。

但我们还在继续摸索“最佳习惯”本身。比如 observer 面板和 TUI 对输出路由事件的展示，还没有 channel 流量那么丰满；条件式边目前还是得靠 channel，因为输出路由不会分支，而一个小型 `when:` 过滤器到底值不值得进框架，我们更想先通过真实使用去理解。再比如内容模式（只发 last_round，还是 all_rounds，还是发摘要）以后也可能变得有用，尤其是某些流水线想把推理痕迹也串过去的时候——现在还没到拍板的时候。完整开放问题都在 [ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md)。

如果一个父 creature 自己就能把任务拆开并纵向委派，那优先还是 **sub-agent** —— 这通常是大多数“我只是想隔离上下文”需求下更简单的解。真正需要多个独立 creatures 协作，而且你还希望每个 creature 单独拿出来也能跑时，再上 terrarium。

## 排错

- **团队卡住了，没有消息在动。** 最常见原因是：发送方那条边还靠 `send_message`，而 LLM 忘了发。通常有两个修法：
  - 如果这条边本来就是确定性的，直接给它加 `output_wiring:`，让框架自动接线，框架不会忘。
  - 如果这条边本来就该是条件式的，那就继续用 channel，但把发送方 prompt 写得更明确一点。
  同时可以用 `--observe` 看实时 channel 流量。
- **creature 收到 channel 消息却没反应。** 先确认 `listen` 里有这个 channel 名，再检查 `ChannelTrigger` 有没有注册好；`kt terrarium info` 会把 wiring 打出来。
- **root 看不到 creature 在干什么。** 现在有两条路：
  - 走 channel：把 `report_to_root` 加进相关 creature 的 `can_send` 列表里。
  - 走输出路由：在它的 `output_wiring` 里加 `{to: root, with_content: false}`，这样哪怕 creature 从头到尾没调 `send_message`，root 也能收到生命周期 ping。
- **输出路由的目标没收到任何东西。** 先检查目标 creature 是否真的存在于同一个 terrarium 里，而且正在运行。输出路由按 creature 名解析（或者特殊值 `root`）；找不到、没启动时，会记日志然后跳过。
- **creature 一多，启动变慢。** 每个 creature 都会启动自己的 LLM provider 和 trigger manager，所以启动时间大体是线性增长的。

## 另见

- [Creatures](creatures.md)：terrarium 里的每个条目，本质上都是一个 creature。
- [Composition](composition.md)：如果你只需要一个小循环，不需要完整 terrarium，可以看这个 Python 侧方案。
- [以代码方式使用](programmatic-usage.md)：`TerrariumRuntime` 加 `KohakuManager`。
- [Terrarium 概念说明](./concepts/multi-agent/terrarium.md)：为什么 terrarium 会设计成这样。
