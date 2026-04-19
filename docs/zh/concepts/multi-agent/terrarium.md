# Terrarium

## 它是什么

**Terrarium** 是一层纯接线层，用来把几个 creature 一起跑起来。它自己没有 LLM，没有智能，也不做决策。它主要做三件事：

1. 作为 **runtime**，管理各个 creature 的生命周期。
2. 持有一组 **shared channels**，让这些 creature 彼此通信。
3. 提供框架级的**输出路由**，让一个 creature 的回合结束输出能自动送进另一个 creature 的事件队列。

这就是它全部的职责。

```
  +---------+       +---------------------------+
  |  User   |<----->|        Root Agent         |
  +---------+       |  (terrarium tools, TUI)   |
                    +---------------------------+
                          |               ^
            sends tasks   |               |  observes
                          v               |
                    +---------------------------+
                    |     Terrarium Layer       |
                    |   (pure wiring, no LLM)   |
                    +-------+----------+--------+
                    |  swe  | reviewer |  ....  |
                    +-------+----------+--------+
```

## 它为什么存在

只要 creature 是可移植的——单独就能跑，同一份配置脱离团队也能用——你就需要一种组合方式，让它们协作，但又不用互相知道对方的存在。Terrarium 就是干这个的。

这里有个不变条件：creature 不会知道自己在 terrarium 里。它只监听 channel 名，也只往 channel 名发消息。就这些。把它从 terrarium 里拿出来，它照样能单独运行。

## 我们怎么定义它

Terrarium 配置：

```yaml
terrarium:
  name: my-team
  root:                         # optional; user-facing agent outside the team
    base_config: "@pkg/creatures/general"
    system_prompt_file: prompts/root.md   # 这个团队专用的委派 prompt
  creatures:
    - name: swe
      base_config: "@pkg/creatures/swe"
      output_wiring: [reviewer]           # 确定性边：回合结束自动送 reviewer
      channels:
        listen:    [tasks, feedback]
        can_send:  [status]
    - name: reviewer
      base_config: "@pkg/creatures/swe"   # reviewer 角色靠 prompt 定义，不一定要单独的 creature
      system_prompt_file: prompts/reviewer.md
      channels:
        listen:    [status]
        can_send:  [feedback, status]      # 条件分支：通过 / 打回，继续放在 channel 上
  channels:
    tasks:    { type: queue }
    feedback: { type: queue }
    status:   { type: broadcast }
```

runtime 会自动给每个 creature 建一个 queue，名字就是它自己的名字，这样别的 creature 可以直接给它发私信。如果定义了 root，还会额外建一个 `report_to_root` channel。

## 我们怎么实现它

- `terrarium/runtime.py` — `TerrariumRuntime` 按固定顺序启动：先建 shared channels，再建 creatures，再接上 triggers，最后才构建 root，而且这时还不启动。
- `terrarium/factory.py` — `build_creature` 负责加载 creature 配置（支持 `@pkg/...` 解析），用 shared environment 和私有 session 创建 `Agent`，给每个 listen channel 注册一个 `ChannelTrigger`，再往 system prompt 里注入一段 channel 拓扑说明。
- `terrarium/hotplug.py` — 支持在运行时调用 `add_creature`、`remove_creature`、`add_channel`、`remove_channel`。
- `terrarium/observer.py` — 提供 `ChannelObserver`，做非破坏式监控。仪表盘之类的工具可以旁观，但不会把消息消费掉。
- `terrarium/api.py` — `TerrariumAPI` 是面向编程调用的统一入口；内置的 terrarium 管理工具（`terrarium_create`、`creature_start`、`terrarium_send` 等）都走它。

## 所以你可以做什么

- **显式的专家团队。** 让两个 `swe` creature 通过 `tasks` / `feedback` / `status` 这组拓扑协作，其中 reviewer 这个角色可以只靠 prompt 区分。
- **面向用户的 root agent。** 见 [Root agent](root-agent.md)。用户只和一个 agent 对话，由它去调度整个团队。
- **用输出路由做确定性流水线边。** 你可以在 creature 配置里声明：它每轮结束后的输出，自动流向下一个阶段；不用赌 LLM 会不会记得 `send_message`。
- **热插拔专家。** 会话进行到一半时加一个新 creature，不用重启；现有 channels 会直接把它接进来。
- **非破坏式监控。** 给 queue channel 挂一个 `ChannelObserver`，就能看到每条消息，同时不和真正的消费者抢消息。

## 输出路由和 channel 一起用

channel 依然是处理**条件式、可选式消息流**的标准做法：比如 reviewer 要在“通过”和“打回重改”之间二选一，状态广播谁都可以看看，或者团队内部有个群聊边栏。这些都依赖 creature 自己调用 `send_message`。

输出路由是另一条框架级通路：某个 creature 在配置里声明 `output_wiring`，那么它每轮结束时，runtime 就会直接往目标 creature 的事件队列里发一个 `creature_output` TriggerEvent。没有 channel，也没有 tool call——它走的是普通 trigger 一样的事件路径。

所以，**确定性的流水线边**就用输出路由，比如“这一步做完永远交给下一步”；而条件分支、广播、观察这些输出路由表达不了的情况，继续用 channel。两种机制放在同一个 terrarium 里完全没问题——kt-biome 的 `auto_research` 和 `deep_research` 就是这么混着用的。

具体配置长什么样，见 [Terrariums 指南里的输出路由](/zh/terrariums.md#输出路由)。

## 现在的定位，实话实说

我们现在把 terrarium 看成一种**横向多智能体的候选架构**，而不是已经完全定型的唯一标准答案。今天能跑起来的零件已经够完整了：输出路由 + channels + 热插拔 + 观察 + 给 root 的生命周期信号，kt-biome 里的 terrarium 也都在端到端地验证这套组合。我们还在继续摸索的，是使用习惯本身：什么时候优先 wiring，什么时候继续 channel；条件分支怎么写才不用手搓很多 channel plumbing；UI 里怎么把 wiring 活动显示得跟 channel 流量一样清楚。

真正适合上 terrarium 的，是那种流程本来就确实由多个 creatures 协作完成，而且你希望这些 creatures 保持可移植、单独也能跑的场景。要是任务天然就是一个 creature 内部做纵向拆分，那 sub-agent 还是更简单，也通常更顺手。两条路都正当，框架不会替你选。

完整的后续探索方向（比如 wiring 事件在 UI 中的呈现、条件式 wiring、内容模式、wiring 热插拔），见 [ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md)。

## 别把它想死了

没有 root 的 terrarium 完全成立，就是无头协作工作流。没有 creatures 的 root，也只是一个带特殊工具的独立 agent。一个 creature 在不同运行里可以属于零个、一个，或者多个 terrarium。Terrarium 不会改变 creature 本身。

## 另见

- [多智能体概览](README.md) —— 纵向和横向的区别。
- [Root agent](root-agent.md) —— 团队之外、面向用户的 creature。
- [Channel](../modules/channel.md) —— terrarium 赖以构成的基础单元。
- [ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md) —— terrarium 后面会往哪走。
