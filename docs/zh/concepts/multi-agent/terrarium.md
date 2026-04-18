# Terrarium

## 它是什么

**Terrarium** 是一层纯粹的编排层，用来把几个 creature 一起跑起来。它自己没有 LLM，没有智能，也不做决策。它只做两件事：

1. 作为 **runtime**，管理各个 creature 的生命周期。
2. 持有一组 **共享 channel**，让这些 creature 彼此通信。

它的职责就这么多。

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

一旦 creature 变得可移植——单独就能运行，同一份配置也能脱离团队独立使用——你就需要一种组合方式，让它们协作，但不用彼此感知对方。Terrarium 就是干这个的。

这里有个不变条件：creature 永远不知道自己正处在 terrarium 里。它只会监听 channel 名，也只会向 channel 名发送消息，仅此而已。把它从 terrarium 里拿出来，它还是能作为独立 creature 运行。

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

runtime 会自动为每个 creature 创建一个 queue，名字就是它自己的名字，这样其他 creature 可以直接给它发私信。要是定义了 root，还会额外创建一个 `report_to_root` channel。

## 我们怎么实现它

- `terrarium/runtime.py` — `TerrariumRuntime` 按固定顺序编排启动流程：先创建共享 channel，再创建 creature，然后接上 trigger，最后才构建 root，而且此时还不启动。
- `terrarium/factory.py` — `build_creature` 负责加载 creature 配置（支持 `@pkg/...` 解析），用共享 environment 和私有 session 创建 `Agent`，为每个监听的 channel 注册一个 `ChannelTrigger`，并把一段 channel 拓扑说明注入 system prompt。
- `terrarium/hotplug.py` — 支持在运行时调用 `add_creature`、`remove_creature`、`add_channel`、`remove_channel`。
- `terrarium/observer.py` — 提供 `ChannelObserver`，用于非破坏式监控，仪表盘之类的工具可以旁观，但不会把消息消费掉。
- `terrarium/api.py` — `TerrariumAPI` 是面向编程使用的统一入口；内置的 terrarium 管理工具（`terrarium_create`、`creature_start`、`terrarium_send` 等）都经过它。

## 因此你能做什么

- **显式的专家团队。** 让 `swe` creature 和 `reviewer` creature 通过 `tasks` / `review` / `status` 这组 channel 拓扑协作。
- **面向用户的 root agent。** 见 [root-agent](/concepts/multi-agent/root-agent.md)（英文）。用户只和一个 agent 对话，由它去调度整个团队。
- **热插拔专家。** 会话进行到一半时加一个新 creature，不用重启；现有 channel 会直接把它接进来。
- **非破坏式监控。** 给 queue channel 挂一个 `ChannelObserver`，就能看到每条消息，同时不和真正的消费者抢消息。

## 说实话

Terrarium 还是实验性的。眼下最大的限制是：一个 terrarium 能不能推进，取决于每个 creature 是否把自己的输出送到正确的 channel。模型要是没按指令来——这事确实会发生——整个团队就可能卡住。

[ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md) 里已经写了后续计划：

- **可配置的自动轮次输出路由** — 让用户指定一个 channel，自动接收某个 creature 在一轮中的最新消息。
- **root 生命周期观测** — 让 root 能看到完成信号，也能检查 channel 活动。
- **配置优先的自动化** — 新增的自动化能力都保持为可选开启。
- **动态 terrarium 管理** — 让 root 能在运行时新增或移除 creature。

在这些能力落地前，只要能选，优先用纵向的多智能体，也就是 sub-agent。Terrarium 现在也能用，但更适合流程已经写得很明确、而且你能相信 creature 会按 prompt 行事的场景。

## 不要被限制住

没有 root 的 terrarium 完全说得通，这就是无头的协作工作流。没有 creature 的 root，也只是一个带特殊工具的独立 agent。一个 creature 在不同运行里可以属于零个、一个，或者多个 terrarium——terrarium 不会改变 creature 本身。

## 另见

- [多智能体概览](/concepts/multi-agent/README.md)（英文）— 纵向和横向的区别。
- [Root agent](/concepts/multi-agent/root-agent.md)（英文）— 团队之外、面向用户的 creature。
- [Channel](/concepts/modules/channel.md)（英文）— terrarium 赖以构成的基础单元。
- [ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md) — terrarium 后面会往哪走。
