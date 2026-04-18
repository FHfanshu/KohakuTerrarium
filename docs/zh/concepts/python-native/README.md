# Python 原生

KohakuTerrarium 里，creature 的每个模块都是 Python 类。agent 是异步 Python 对象。terrarium 是 Python 运行时。plugin 是 Python 类。tool 也是 Python 类。组合代数则是一套 Python API。

这不是巧合，是框架刻意保持的一个特性：既然一切都是 Python，agent 和它的各个部分就能作为值放进*别的*部分里。plugin 可以内嵌一个 agent。trigger 可以内嵌一个 agent。tool 也可以内嵌一个 agent。很多模式就是这么来的，比如更聪明的 guard、会自适应的 watcher、无缝接上的 memory。它们往往只要几十行组合代码，不用再造一套新框架。

这一节有两篇文档：

- [Agent 作为 Python 对象](/concepts/python-native/agent-as-python-object.md)（英文）—— 解释“agent 就是 Python”意味着什么，以及它能解开什么限制。
- [组合代数](/concepts/python-native/composition-algebra.md)（英文）—— 用来把 agent 串成流水线的 API（`>>`、`&`、`|`、`*`、`.iterate`）。

先读第一篇，理解原则。第二篇只在你打算用 Python 写 agent 流水线时再看；如果你写的是 creature 配置，可以跳过。