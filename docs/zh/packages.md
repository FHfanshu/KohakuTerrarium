# Package

给想在多个项目之间共用 creature、terrarium、tool 或 plugin 的人看。

KohakuTerrarium 的 package 就是一个带 `kohaku.yaml` 清单的目录。里面可以放 creatures、terrariums、自定义 tools、plugins，还有 LLM presets。运行 `kt install` 之后，它会被装到 `~/.kohakuterrarium/packages/<name>/`。之后你就可以用 `@<name>/path` 这种写法去引用里面的内容。

概念预读：[boundaries](../concepts/boundaries.md)。package 这一层，主要就是为了让“把能复用的东西拆出来分享”这件事更省事。

## 官方包：`kt-defaults`

很多人第一个装的 package 都是 `kt-defaults`。这是官方示例包，里面带了 `swe`、`reviewer`、`researcher`、`ops`、`creative`、`general`、`root` 这些 creatures，也有 `swe_team`、`deep_research` 这样的 terrariums，还附带了一些 plugins。

```bash
kt install https://github.com/Kohaku-Lab/kt-defaults.git
kt run @kt-defaults/creatures/swe
```

如果你要做自己的 package，先拿 `kt-defaults` 当参考最直接。

## 清单：`kohaku.yaml`

```yaml
name: my-pack
version: "0.1.0"
description: "My shared agent components"

creatures:
  - name: researcher           # folder at creatures/researcher/

terrariums:
  - name: research_team        # folder at terrariums/research_team/

tools:
  - name: my_tool
    module: my_pack.tools.my_tool
    class: MyTool

plugins:
  - name: my_guard
    module: my_pack.plugins.my_guard
    class: MyGuard

llm_presets:
  - name: my-custom-model

python_dependencies:
  - httpx>=0.27
  - pymupdf>=1.24
```

目录结构：

```
my-pack/
  kohaku.yaml
  creatures/researcher/config.yaml
  terrariums/research_team/config.yaml
  my_pack/                     # installable python package
    __init__.py
    tools/my_tool.py
    plugins/my_guard.py
```

Python 模块按点号路径解析，比如 `my_pack.tools.my_tool:MyTool`。配置路径则用 `@my-pack/creatures/researcher` 这种写法。

如果声明了 `python_dependencies`，`kt install` 也会顺手把这些 Python 依赖装上。

## 安装方式

### Git URL（clone）

```bash
kt install https://github.com/you/my-pack.git
```

会 clone 到 `~/.kohakuterrarium/packages/my-pack/`。之后可以用 `kt update my-pack` 更新。

### 本地路径（复制）

```bash
kt install ./my-pack
```

会把整个目录复制进去。后面要更新，要么重新跑一次 `kt install`，要么直接去改复制后的那份。

### 本地路径（editable）

```bash
kt install ./my-pack -e
```

这会写一个 `~/.kohakuterrarium/packages/my-pack.link`，指向源码目录。你改源码，效果会马上生效，不用重新安装。开发时反复调这个最好用。

### 卸载

```bash
kt uninstall my-pack
```

## `@pkg/path` 怎么解析

`@my-pack/creatures/researcher` 的解析规则是：

- 如果有 `my-pack.link`，就跟着它指向的目录走。
- 否则就去 `~/.kohakuterrarium/packages/my-pack/creatures/researcher/` 找。

`kt run`、`kt terrarium run`、`kt edit`、`kt update`、`base_config:` 继承，还有代码里的 `Agent.from_path(...)`，都用这套规则。

## 查看和发现命令

```bash
kt list                         # installed packages + local agents
kt info path/or/@pkg/creature   # details of one config
kt extension list               # all tools/plugins/presets from all packages
kt extension info my-pack       # package metadata + what it ships
```

想快速看看当前环境里到底装了哪些扩展，用 `kt extension list` 最省事。

## 编辑已安装的配置

```bash
kt edit @my-pack/creatures/researcher
```

它会在 `$EDITOR` 里打开 `config.yaml`；如果没设，就按 `$VISUAL`、`nano` 的顺序往后试。editable 安装会直接改源码，普通安装改的是 `~/.kohakuterrarium/packages/` 下面那份副本。

## 发布

1. 把仓库推到 git 上。GitHub、GitLab、自建仓库都行，只要 `git clone` 能拉下来。
2. 打版本标签：`git tag v0.1.0 && git push --tags`。
3. 每次发版时，记得把 `kohaku.yaml` 里的 `version:` 一起更新。
4. 把 URL 发给别人：`kt install https://your/repo.git`。

这里没有中心注册表。package 说到底，就是一个带 `kohaku.yaml` 的 git 仓库。

### 版本管理

`version:` 最好和 git tag 对齐。`kt update` 底层其实就是跑 `git pull`；如果使用方固定在某个 tag，也可以自己手动切过去：

```bash
cd ~/.kohakuterrarium/packages/my-pack
git checkout v0.1.0
```

## 运行时怎么发现扩展

框架加载 creature 时，会先去 creature 自己的本地配置里找 tool 和 plugin 名称，再去已安装 package 的清单里查。package 里声明的 tool，会通过配置里的 `type: package` 暴露出来：

```yaml
tools:
  - name: my_tool
    type: package          # resolved through the `tools:` list in kohaku.yaml
```

所以，只要两个 package 都装了，一个 package 里的 creature 就可以引用另一个 package 里声明的 tool。

## 排错

- **`@my-pack/...` 解析失败。** 先用 `kt list` 确认 package 已经装上了。editable 安装的话，再检查 `.link` 文件指向的目录还在不在。
- **`kt update my-pack` 提示 "skipped"。** editable 安装和非 git package 都不能用 `kt update` 更新。前者直接改源码，后者重新安装。
- **`python_dependencies` 没装上。** 确认 `kt install` 在当前环境里有安装包的权限，比如用 virtualenv，或者用 `pip install --user`。
- **package 里的 tool 把内置 tool 挡住了。** 实际上内置 tool 的解析优先级更高。你要是想让自己的 tool 生效，就换个名字。

## 另见

- [Creatures](creatures.md) —— 怎么打包 creature。
- [Custom Modules](custom-modules.md) —— 怎么写要随 package 一起发布的 tools 和 plugins。
- [Reference / CLI](../reference/cli.md) —— `kt install`、`kt list`、`kt extension`。
- [`kt-defaults`](https://github.com/Kohaku-Lab/kt-defaults) —— 参考 package。
