# 概念

概念文档教心智模型。不是参考 — 字段名、签名、命令在[参考](/reference/README.md)。不是指南 — 任务式指令在[指南](/guides/README.md)。目的是让你摸其他文档时觉得*显而易见*。

如果概念文档读起来像"这里是一堆类"，出问题了。在 issue 里告诉我们。

## 阅读路径

不用按顺序读。按你来这里的原因选路径。

### 评估者（20分钟）

想知道这个框架是什么、适不适合你。

1. [为什么 KohakuTerrarium](/concepts/foundations/why-kohakuterrarium.md)（英文）
2. [什么是 agent](/concepts/foundations/what-is-an-agent.md)（英文）
3. [组合 agent](/concepts/foundations/composing-an-agent.md)（英文）
4. [边界](/concepts/boundaries.md)（英文）

### 构建者（1小时）

想构建不在 `kt-defaults` 的 creature。

1. 上面的评估者路径
2. [模块概览](/concepts/modules/README.md)（英文） → 按需读每个模块
3. [Agent 作为 Python 对象](/concepts/python-native/agent-as-python-object.md)（英文）
4. [模式](/concepts/patterns.md)（英文）
5. [组合代数](/concepts/python-native/composition-algebra.md)（英文）

### 多智能体用户

想跑 creature 团队。

1. 从构建者路径开始。
2. [多智能体概览](/concepts/multi-agent/README.md)（英文）
3. [Terrarium](/concepts/multi-agent/terrarium.md)（英文）
4. [Root agent](/concepts/multi-agent/root-agent.md)（英文）
5. [Channel](/concepts/modules/channel.md)（英文）

### 贡献者 / 深度阅读

想改框架本身。

1. foundations 里的所有。
2. 每个模块文档。
3. impl-notes 里的每篇（英文）。
4. 然后 dev 部分的 internals（英文）。

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
└── glossary.md          通俗英文一段定义。
```

术语卡住时，glossary（英文）最快。

## 概念文档承诺

- **推导，不是列表。** 每个模块有理由。
- **没有模块是必须的。** 每篇文档结尾说*不要被限制*。
- **诚实说明粗糙部分。** 框架实验性的地方文档说明并链接 ROADMAP。
- **教学，不是编目。** 编目见参考。

## 参考

- [指南](/guides/README.md) — 任务式 how-to。
- [参考](/reference/README.md) — 命令、API、字段的穷举式查表。
- [开发](/dev/README.md)（英文） — 贡献者内部。