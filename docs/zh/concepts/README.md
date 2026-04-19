# 概念

这部分主要讲怎么理解这个框架。字段名、命令、签名那些细节，去看[参考](/reference/README.md)。想照着步骤做事，去看[指南](/zh/guides-README.md)。这里要解决的是：你先把脑子里的图搭起来，后面读别的文档才不费劲。

如果你读完只记住了一堆类名和模块名，那这页就没写好。可以直接提 issue。

## 阅读路径

不用按顺序读。按你来这里的原因选路径。

### 评估者（20分钟）

想知道这个框架是什么、适不适合你。

1. [为什么 KohakuTerrarium](/concepts/foundations/why-kohakuterrarium.md)
2. [什么是 agent](/concepts/foundations/what-is-an-agent.md)
3. [组合 agent](/concepts/foundations/composing-an-agent.md)
4. [边界](/concepts/boundaries.md)

### 构建者（1小时）

想构建不在 `kt-biome` 的 creature。

1. 上面的评估者路径
2. [模块概览](/concepts/modules/README.md) → 按需读每个模块
3. [Agent 作为 Python 对象](/concepts/python-native/agent-as-python-object.md)
4. [模式](/concepts/patterns.md)
5. [组合代数](/concepts/python-native/composition-algebra.md)

### 多智能体用户

想跑 creature 团队。

1. 从构建者路径开始。
2. [多智能体概览](/concepts/multi-agent/README.md)
3. [Terrarium](/concepts/multi-agent/terrarium.md)
4. [Root agent](/concepts/multi-agent/root-agent.md)
5. [Channel](/concepts/modules/channel.md)

### 贡献者 / 深度阅读

想改框架本身。

1. foundations 里的所有。
2. 每个模块文档。
3. impl-notes 里的每篇。
4. 然后 dev 部分的 internals。

## 结构

```
concepts/
├── foundations/         为什么存在；agent 是什么；如何组合。
├── modules/             creature 的每个模块一篇。
├── python-native/       agent 作为 Python 值；组合代数。
├── multi-agent/         Terrarium + root agent。
├── impl-notes/          值得教的具体实现选择。
├── patterns.md          组合模块会涌现什么。
├── boundaries.md        抽象是默认，不是定律。
└── glossary.md          词汇表，先查词很快。
```

术语卡住时，glossary最快。

## 概念文档承诺

- **不是罗列概念。** 每个模块为什么存在，文档里会说清楚。
- **没有哪一块是圣旨。** 默认这样设计，不代表你只能这样用。
- **哪里还不成熟，就直说。** 文档会标出来，也会给你 ROADMAP。
- **这里讲的是理解，不是查表。** 查表去参考文档。

## 参考

- [指南](/zh/guides-README.md) — 按步骤做事。
- [参考](/reference/README.md) — 查命令、API 和字段。
- [开发](/dev/README.md) — 给贡献者看的内部文档。