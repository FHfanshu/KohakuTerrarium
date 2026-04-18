# `kt install` 与 package 进阶：安装的到底是什么，为什么不是 skill

这篇只讲 package 和 `kt install`。

很多人第一次用 KohakuTerrarium 时，会把下面几件事混在一起：

- `kt install`
- `@pkg/path`
- 自定义 tool / plugin 的复用
- skills 文档

这里先把结论放前面：

> **`kt install` 安装的是 package，不是 skill。**

---

## package 是什么

在这个项目里，package 是一个带 `kohaku.yaml` 的目录。

它可以包含：

- creatures
- terrariums
- 自定义 tools
- plugins
- LLM presets

它本质上是一个 **分发和复用单位**。

也就是说，package 解决的不是“模型怎么理解工具”，而是：

- 一套 creature 配置怎么共享
- 自定义工具和插件怎么复用
- 一整个仓库怎么让别人一条命令装上

---

## `kt install` 实际在做什么

`kt install` 做的事情其实很直接：

- 如果给的是 git URL，就 clone 下来
- 如果给的是本地目录，就复制进去
- 如果加了 `-e`，就做成可编辑链接

安装位置通常在：

```text
~/.kohakuterrarium/packages/<name>/
```

装完之后，你就可以用 `@pkg/path` 引用包里的内容。

例如：

```bash
kt install https://github.com/Kohaku-Lab/kt-defaults.git
kt run @kt-defaults/creatures/swe
```

这里：

- `kt-defaults` 是 package 名
- `@kt-defaults/creatures/swe` 是包内路径引用

---

## `@pkg/path` 到底是什么

像下面这种写法：

```text
@kt-defaults/creatures/swe
```

它不是：

- skill 名
- MCP server 名
- Python 模块路径

它就是一个 **安装后的包内资源路径**。

你可以把它理解成：

- 先找到安装的 package
- 再在 package 目录里定位对应的 creature / terrarium / 配置路径

所以它更接近“包资源引用”，不是“能力类型”。

---

## 为什么说 `kt install` 不是安装 skill

这是最容易误会的点。

`kt install` 安装的是 package。package 里当然可能带来：

- 新的 creature
- 新的 tool
- 新的 plugin
- 新的文档

这些内容最终可能会影响模型能看到哪些工具说明，但这不等于 package 本身就是 skill。

更清楚地说：

- **package**：分发单位
- **tool**：能力单位
- **skill**：给模型看的说明文档单位

三层职责不一样。

---

## 什么时候优先想 package

这些场景更适合先想到 package：

- 想复用别人写好的 creature
- 想把团队内部的一套 agent 模板发给别人
- 想共享一组自定义 plugin / tool / preset
- 想让 `base_config` 继承一套稳定基座

典型例子就是官方的 `kt-defaults`。

它不是一个“skill 包”，而是一套可安装、可引用、可继承的默认内容集合。

---

## 可编辑安装什么时候有用

开发自己的 package 时，`-e` 很实用：

```bash
kt install ./my-pack -e
```

这样做之后：

- 安装目录不会复制整份内容
- 会写一个 `.link` 指向源目录
- 你改源代码或配置后，不用重新安装

适合：

- 迭代 creature 配置
- 调试 package 内的 Python 模块
- 一边改，一边 `kt run` / `kt info` 验证

---

## 一个最小示例

目录结构：

```text
my-pack/
  kohaku.yaml
  creatures/
    helper/
      config.yaml
```

`kohaku.yaml`：

```yaml
name: my-pack
version: "0.1.0"
creatures:
  - name: helper
```

安装：

```bash
kt install ./my-pack -e
```

运行：

```bash
kt run @my-pack/creatures/helper
```

这个例子里，重点不是 skill，也不是 MCP，而是：

- package 怎么组织
- `kt install` 怎么安装
- `@pkg/path` 怎么引用

---

## package 和 MCP 的边界

可以这样区分：

- **package**：把一套内容发给别人
- **MCP**：把外部系统能力接进 agent

一个 package 里当然可以包含 MCP 相关配置模板；但那只是“package 带着配置走”，不等于 package 本身变成了 MCP。

---

## package 和 skills 的边界

也可以这样区分：

- **package**：负责内容分发
- **skills**：负责把工具 / 子智能体说明交给模型

一个 package 里的自定义 tool 最终当然也可能有自己的说明文档；但那只是“这个 package 里包含了某些可被模型读取的文档”，不是“package = skill”。

---

## 推荐继续读什么

- [英文 Packages 指南](../guides/packages.md)
- [配置文件写法](configuration)
- [skills 与 skill_mode 进阶](skills-and-skill-mode-advanced)

---

## 一句话总结

**`kt install` 安装的是 package：它解决的是分发、复用和引用，不是文档注入，也不是 MCP 连接。**
