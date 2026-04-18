# 第一个 Terrarium

**问题：**你想让两个 creature 协作：一个负责写，一个负责审稿；同时还能看到它们之间的消息怎么流转。

**完成后：**你会有一个 terrarium 配置，里面有两个 creatures、两条 channels，并且能在 TUI 里跑起来，直接看到消息从一个传到另一个。

**前提：**先做过[第一个 Creature](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/tutorials/first-creature.md)（英文）。你需要已经安装 `kt-defaults`，并且能用 `kt run` 跑起单个 creature。

Terrarium 只负责连线：它持有 channels，管理 creature 的生命周期。它自己没有 LLM。真正的智能仍然在各个 creature 里面。完整约定见 [terrarium 概念](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/multi-agent/terrarium.md)（英文）。

## 第 1 步：创建目录

```bash
mkdir -p terrariums
```

Terrarium 配置放哪都行。一般会在 creatures 旁边放一个 `terrariums/` 目录。

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
      base_config: "@kt-defaults/creatures/general"
      system_prompt: |
        You are a concise writer. When you receive a message on
        `tasks`, write a short draft and send it to `review` using
        send_message. When you receive feedback, revise and resend.
      channels:
        listen:    [tasks, feedback]
        can_send:  [review]

    - name: reviewer
      base_config: "@kt-defaults/creatures/reviewer"
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

这套连线在做什么：

- `listen` 会给 creature 注册一个 `ChannelTrigger`。消息一旦进入这些 channel，creature 就会被唤醒并看到消息。
- `can_send` 列出 creature 的 `send_message` 工具允许写入哪些 channel。没列在这里的 channel，它发不过去。
- Channels 只在 `channels:` 里声明一次。`queue` 会把每条消息发给一个消费者；`broadcast` 会发给所有监听者。

内联的 `system_prompt:` 会追加到继承来的基础 prompt 后面。教程里这样写，是为了把例子放在一个文件里。实际使用更建议用 `system_prompt_file:`。

## 第 3 步：检查拓扑（可选）

```bash
kt terrarium info terrariums/writer-team.yaml
```

这条命令会打印 creatures、它们监听和发送的 channel 集合，以及 channel 定义。正式运行前先看一眼，能少踩点坑。

## 第 4 步：运行

```bash
kt terrarium run terrariums/writer-team.yaml --mode tui --seed "write a one-paragraph product description for a smart kettle" --seed-channel tasks
```

TUI 打开后，每个 creature 一个标签页，每个 channel 也有一个标签页。`--seed` 会在启动时把你的提示词注入到 `seed-channel` 指定的 channel 里，默认是 `seed`，这里改成了 `tasks`。接着 writer 被唤醒，写出草稿并发到 `review`；reviewer 被唤醒，给出审阅意见并发到 `feedback`；writer 再醒一次，继续修改。

你可以在 channel 标签页里看原始消息流，也可以在 creature 标签页里看各自的推理过程。

## 第 5 步：先知道它的限制

这种横向多 agent 结构有个很实际的问题：**能不能继续推进，取决于每个 creature 会不会把输出发到正确的 channel。** 如果模型忘了调用 `send_message`，对应 channel 就是空的，整个团队会卡住。

现在常用的办法有两个：

1. **把提示写得更明确。** 直接告诉 creature 什么时候该往哪个 channel 发消息。上面的内联 prompt 就是这么做的。
2. **加一个 root agent。** root creature 在 terrarium *外面*，它持有 terrarium 管理工具。它接收用户输入、给团队下种子、观察 channels，也会在 creatures 卡住时推一把。可以看看 `@kt-defaults/creatures/root` 和 `swe_team` terrarium 这个完整例子。模式说明见 [root agent 概念](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/multi-agent/root-agent.md)（英文）。

例子：加一个 root：

```yaml
terrarium:
  name: writer_team
  root:
    base_config: "@kt-defaults/creatures/root"
  # ... creatures and channels as before
```

这样一来，TUI 会把 root agent 挂到主标签页上，你直接和它对话；它再通过 terrarium tools 去调度 writer 和 reviewer。

## 第 6 步：Terrarium 后面会补什么

自动路由（可配置，例如“creature 的最后一条消息总是发到 channel X”）、root 的生命周期观察，以及动态 creature 管理，都在路线图里。现在这些能力还没落地，所以只要事情比较重要，还是优先用显式 prompt，或者上 root creature。完整说明见 [ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md)（英文）里的 terrarium 部分。

## 你学到的内容

- Terrarium 负责连线，不负责智能。
- Creatures 仍然是独立的；terrarium 只规定谁能听到什么、谁能往哪发消息。
- 横向多 agent 这套是能工作的，但路由要靠明确提示，当前最常见的问题就是卡住。
- 如果你想要一个面向用户的统一协调者，实用做法是加一个 root creature。

## 接下来可以看什么

- [Terrarium 概念](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/multi-agent/terrarium.md)（英文）—— 约定和边界。
- [Root agent 概念](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/multi-agent/root-agent.md)（英文）—— 面向用户的 creature。
- [Terrariums 指南](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/guides/terrariums.md)（英文）—— 实际用法参考。
- [Channel 概念](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/docs/concepts/modules/channel.md)（英文）—— `queue` 和 `broadcast` 的区别、observers，以及 channels 如何跨模块边界。
