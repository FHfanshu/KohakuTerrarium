# 第一个 Terrarium

你想让两个 creature 配合起来干活：writer 先写，reviewer 再提意见。你还想亲眼看到消息怎么在它们之间来回传。

这篇做完，你手里会有一个 terrarium 配置：里面有两个 creatures、两个 channels，可以在 TUI 里跑起来，消息会从一个传到另一个。

前提是：先看过[第一个 Creature](first-creature.md)。你还得已经装好 `kt-biome`，并且能用 `kt run` 跑单个 creature。

terrarium 只管接线。它持有 channels，也负责 creatures 的生命周期；自己没有 LLM。真正做判断、出主意的，还是各个 creature。完整约定见 [Terrarium 概念](../concepts/multi-agent/terrarium.md)。

## 第 1 步：建文件夹

```bash
mkdir -p terrariums
```

terrarium 配置其实放哪都行。一般会放在和 creatures 并列的 `terrariums/` 目录里。

## 第 2 步：写 terrarium 配置

`terrariums/writer-team.yaml`：

```yaml
# Writer + reviewer team.
#   tasks    -> writer  -> review  -> reviewer
#                       <- feedback <- reviewer

terrarium:
  name: writer_team

  creatures:
    - name: writer
      base_config: "@kt-biome/creatures/general"
      system_prompt: |
        You are a concise writer. When you receive a message on
        `tasks`, write a short draft and send it to `review` using
        send_message. When you receive feedback, revise and resend.
      channels:
        listen:    [tasks, feedback]
        can_send:  [review]

    - name: reviewer
      base_config: "@kt-biome/creatures/general"
      system_prompt: |
        You critique drafts. When you receive a message on `review`,
        reply with one or two concrete improvement suggestions on
        `feedback` using send_message. If the draft is good, say so.
      channels:
        listen:    [review]
        can_send:  [feedback]

  channels:
    tasks:    { type: queue, description: "Incoming work for the writer" }
    review:   { type: queue, description: "Drafts sent to the reviewer" }
    feedback: { type: queue, description: "Review notes sent back" }
```

这套接线在做什么：

- `listen` 会给 creature 挂上 `ChannelTrigger`。消息一到这些 channel，creature 就会被唤醒并看到这条消息。
- `can_send` 列出这个 creature 的 `send_message` 工具允许写到哪些 channel。没列进去的 channel，它发不过去。
- Channels 只在 `channels:` 里定义一次。`queue` 会把每条消息交给一个消费者；`broadcast` 会发给所有 listener。

这里把 `system_prompt:` 直接写在配置里，是为了让教程放在一页里就能看完。真要长期用，还是更推荐 `system_prompt_file:`。

## 第 3 步：看一眼拓扑图（可选）

```bash
kt terrarium info terrariums/writer-team.yaml
```

它会打印出有哪些 creatures、各自监听和发送哪些 channels，以及 channel 的定义。正式跑之前先看一眼，比较稳妥。

## 第 4 步：跑起来

```bash
kt terrarium run terrariums/writer-team.yaml --mode tui --seed "write a one-paragraph product description for a smart kettle" --seed-channel tasks
```

TUI 打开后，每个 creature 一页，每个 channel 也有一页。`--seed` 会在启动时把你的提示词塞到 `seed-channel` 指定的 channel 里；默认是 `seed`，这里我们改成了 `tasks`。接下来 writer 被唤醒，写出草稿，发到 `review`；reviewer 被唤醒，给出意见，发到 `feedback`；writer 再醒一次，继续改。

你可以看 channel 标签页里的原始消息流，也可以看 creature 标签页里各自的推理过程。

## 第 5 步：把交接改成更稳的输出路由

channel 很适合做条件式 / 可选式 / 广播式消息流——比如 reviewer 到底是“通过”还是“打回重写”，这确实是一个应该留在 channel 里的分支判断。但 writer → reviewer 这条边，其实是**确定性的**：writer 每次一轮结束，reviewer 都应该看到它刚写出来的内容。继续依赖 writer 的 LLM 记得调用 `send_message("review", ...)`，就是这类拓扑最常见的故障点。

框架现在提供了一个更直接的办法：**输出路由**。你在 creature 配置里把这条边声明出来，runtime 就会在回合结束时，直接往目标 creature 的事件队列里塞一个 `creature_output` 事件——两边都不需要自己调 `send_message`。

把 `terrariums/writer-team.yaml` 改成这样：

```yaml
terrarium:
  name: writer_team
  creatures:
    - name: writer
      base_config: "@kt-biome/creatures/general"
      system_prompt: |
        You write short product copy. You receive a brief on `tasks`
        and a critique on `feedback`. When you receive feedback, revise
        your draft based on it.
      output_wiring:
        - reviewer                # 每次 writer 回合结束 -> reviewer
      channels:
        listen: [tasks, feedback]
        can_send: []              # 不再需要自己往 `review` 发
    - name: reviewer
      base_config: "@kt-biome/creatures/general"
      system_prompt: |
        You are a strict reviewer. The writer's draft will arrive as a
        creature_output event. If the draft is good, send "APPROVED:
        <draft>" on `feedback`. If not, send specific revision requests
        on `feedback`.
      channels:
        listen: []                # writer 的输出通过 wiring 收到
        can_send: [feedback]      # reviewer 的决定是条件式的，继续放 channel
  channels:
    tasks:    { type: queue }
    feedback: { type: queue }
```

这次改动里最关键的点：

- writer 的 `output_wiring: [reviewer]`，取代了原来 writer 主动往 `review` channel 发消息这件事。
- `review` channel 整条边都删掉了，因为这段交接现在由框架自动接线。
- reviewer 依然用 `feedback` 这个 channel 回给 writer，因为“通过还是修改”本来就是条件分支，输出路由自己不会分支。

现在再跑一次，这个来回会稳很多：即使 writer 没有记得调用 `send_message`，输出路由也照样会在每轮结束时自动触发。

## 第 6 步：需要交互入口的话，再加 root（可选）

有了 channel + 输出路由，你已经有一个能自己协作的无头小团队了。如果你还想要一个统一的对话入口——用户只跟一个 agent 说话，由它去驱动整个团队——那就再加一个 **root**：

```yaml
terrarium:
  name: writer_team
  root:
    base_config: "@kt-biome/creatures/general"
    system_prompt_file: prompts/root.md   # 这个团队专用的委派 prompt
  creatures:
    - ...
```

在 terrarium yaml 旁边新建一份 `prompts/root.md`。它主要写委派风格和团队口吻就够了；框架会自动补上一段团队拓扑说明，把有哪些 creatures、有哪些 channels 写进去，同时还会强制注入 terrarium 管理工具（`terrarium_send`、`creature_status`、`terrarium_history` 等）。

这样一来，TUI 主标签页挂的就是 root。你直接跟 root 说话，root 再去驱动 writer 和 reviewer。更完整的模式说明见 [Root agent 概念](../concepts/multi-agent/root-agent.md)。

## 你学到了什么

- terrarium 只负责接线，不负责思考。
- creatures 还是各自独立；terrarium 只是规定谁能听见什么、谁能往哪发消息，以及谁的回合结束输出要自动流向谁。
- 横向协作现在有两种机制，而且可以混着用：
  - **channel** —— 适合条件分支、可选消息、广播。
  - **输出路由** —— 适合确定性的流水线边；每轮结束自动触发，不依赖 creature 自己记得发。
- root 是可选的。做无头工作流可以不要；想给用户一个统一入口，就加上它。

## 接下来可以看什么

- [Terrarium 概念](../concepts/multi-agent/terrarium.md) —— terrarium 的约定边界。
- [Root agent 概念](../concepts/multi-agent/root-agent.md) —— 面向用户的那个 creature。
- [Terrariums 指南](../terrariums.md) —— 更偏实操的参考文档。
- [Channel 概念](../concepts/modules/channel.md) —— `queue` 和 `broadcast` 的区别、observers，以及 channel 怎么跨模块。