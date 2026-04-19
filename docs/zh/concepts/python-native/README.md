# Python-native

KohakuTerrarium 里的每个 creature module 都是 Python class。agent 是异步 Python object。terrarium 是 Python runtime。plugin 是 Python class。tool 也是 Python class。compose algebra 则是一套 Python API。

这是框架本身的有意设计：既然所有东西都是 Python，agent 和它的各个部分就都能当成值，塞进*别的*部分里。plugin 里可以嵌 agent，trigger 里可以嵌 agent，tool 里也可以嵌 agent。很多有意思的模式——比如 smart guard、adaptive watcher、seamless memory——因此不用另起一套框架，写几十行组合代码就够了。

这一节有两篇文档：

- [Agent as a Python object](agent-as-python-object.md) —— 讲 first-class value 这件事，也就是“agents are Python”到底能让你做什么。
- [Composition algebra](composition-algebra.md) —— 讲把 agent 拼成 pipeline 的那套 API（`>>`, `&`, `|`, `*`, `.iterate`）。

先看第一篇，理解核心思路。第二篇只有在你打算直接用 Python 写 agent pipeline 时才需要看；如果你平时写的是 creature config，可以先跳过。