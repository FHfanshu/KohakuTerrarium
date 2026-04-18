# Terrarium

## 它是什么

**Terrarium** 是一层纯接线层，用来把几个 creature 一起跑起来。它自己没有 LLM，没有智能，也不做决策。它只做两件事：

1. 作为 **runtime**，管理各个 creature 的生命周期。
2. 持有一组 **shared channels**，让这些 creature 彼此通信。

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
    base_config: "@pkg/creatures/root"
  creatures:
    - name: swe
      base_config: "@pkg/creatures/swe"
      channels:
        listen:    [tasks]
        can_send:  [review, status]
    - name: reviewer
      base_config: "@pkg/creatures/reviewer"
      channels:
        listen:    [review]
        can_send:  [status]
  channels:
    tasks:    { type: queue }
    review:   { type: queue }
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

- **显式的专家团队。** 让 `swe` creature 和 `reviewer` creature 通过 `tasks` / `review` / `status` 这组 channel 拓扑协作。
- **面向用户的 root agent。** 见 [Root agent](root-agent.md)。用户只和一个 agent 对话，由它去调度整个团队。
- **热插拔专家。** 会话进行到一半时加一个新 creature，不用重启；现有 channels 会直接把它接进来。
- **非破坏式监控。** 给 queue channel 挂一个 `ChannelObserver`，就能看到每条消息，同时不和真正的消费者抢消息。

## 老实说

Terrarium 还是实验性的。眼下最大的限制是，一个 terrarium 能不能继续跑下去，要看每个 creature 会不会把自己的输出送到对的 channel。模型要是没按指令来——这事确实会发生——整个团队就可能卡住。

[ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md) 里写了后续计划：

- **可配置的自动轮次输出路由** — 让用户指定一个 channel，自动接收某个 creature 在一轮里的最新消息。
- **root 生命周期观察** — 让 root 能看到完成信号，也能检查 channel 活动。
- **配置优先的自动化** — 新增的自动化能力都保持为可选开启。
- **动态 terrarium 管理** — 让 root 能在运行时新增或移除 creature。

在这些能力落地前，只要能选，优先用纵向多智能体，也就是 sub-agent。Terrarium 现在也能用，但更适合流程已经写得很清楚，而且你也相信 creature 会按 prompt 行事的场景。

## 别把它想死了

没有 root 的 terrarium 完全成立，就是无头协作工作流。没有 creatures 的 root，也只是一个带特殊工具的独立 agent。一个 creature 在不同运行里可以属于零个、一个，或者多个 terrarium。Terrarium 不会改变 creature 本身。

## 另见

- [多智能体概览](README.md) —— 纵向和横向的区别。
- [Root agent](root-agent.md) —— 团队之外、面向用户的 creature。
- [Channel](../modules/channel.md) —— terrarium 赖以构成的基础单元。
- [ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md) —— terrarium 后面会往哪走。
