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
      base_config: "@kt-biome/creatures/reviewer"
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

## 第 5 步：先认清它现在的限制

横向多 agent 现在有个很实际的失败点：**每个 creature 得真的把输出发到对的 channel，流程才能往下走。** 如果模型忘了调用 `send_message`，那个 channel 就是空的，整组协作会卡住。

现在能用的办法主要有两个：

1. **把提示词写得更硬一点。** 直接告诉 creature 该往哪个 channel 发、什么时候发。上面那段内联 prompt 就是在干这个。
2. **加一个 root agent。** root creature 在 terrarium 外面，手里有管理 terrarium 的工具。它接收用户输入，给团队播种子，观察各个 channel，哪个 creature 卡住了就推一把。可以看 `@kt-biome/creatures/root` 和 `swe_team` 这个 terrarium。具体模式见 [Root agent 概念](../concepts/multi-agent/root-agent.md)。

例子：加一个 root

```yaml
terrarium:
  name: writer_team
  root:
    base_config: "@kt-biome/creatures/root"
  # ... creatures and channels as before
```

这样一来，TUI 主标签页挂的就是 root agent。你直接和它说话，它再通过 terrarium 工具去调度 writer 和 reviewer。

## 第 6 步：terrarium 接下来会补什么

自动路由（可配置成“creature 的最后一条消息总是发到 channel X”）、root 的生命周期观察、动态 creature 管理，这些都在路线图里。现在它们还没落地，所以只要事情重要，最好还是用明确 prompt，或者直接上 root creature。完整说明见 [ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md) 里的 terrarium 部分。

## 你学到了什么

- terrarium 只负责接线，不负责思考。
- creatures 还是各自独立；terrarium 只是规定谁能听见什么、谁能往哪发消息。
- 横向多 agent 现在能用，但不自动；路由主要靠 prompt，常见故障就是卡住不动。
- 如果你想要一个面向用户的总控，实用做法还是加一个 root creature。

## 接下来可以看什么

- [Terrarium 概念](../concepts/multi-agent/terrarium.md) —— terrarium 的约定边界。
- [Root agent 概念](../concepts/multi-agent/root-agent.md) —— 面向用户的那个 creature。
- [Terrariums 指南](../guides/terrariums.md) —— 更偏实操的参考文档。
- [Channel 概念](../concepts/modules/channel.md) —— `queue` 和 `broadcast` 的区别、observers，以及 channel 怎么跨模块。