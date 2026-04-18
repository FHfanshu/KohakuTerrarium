# Package

给需要在多个项目之间共享 creature、terrarium、tool 或 plugin 的读者。

KohakuTerrarium 的 package 本质上是一个带 `kohaku.yaml` 清单文件的目录。里面可以放 creatures、terrariums、自定义 tools、plugins 和 LLM presets。运行 `kt install` 后，它会被放到 `~/.kohakuterrarium/packages/<name>/`，然后你可以用 `@<name>/path` 引用里面的内容。

概念预读：[boundaries](/concepts/boundaries.md)（英文）。package 这一层，就是框架用来低成本复用和共享组件的方式。

## 官方包：`kt-defaults`

大多数人第一个安装的 package 是 `kt-defaults`。这是官方示例包，里面有 `swe`、`reviewer`、`researcher`、`ops`、`creative`、`general`、`root` 这些 creatures，也有 `swe_team`、`deep_research` 这样的 terrariums，还带了一些 plugins。

```bash
kt install https://github.com/Kohaku-Lab/kt-defaults.git
kt run @kt-defaults/creatures/swe
```

如果你准备做自己的 package，先看看 `kt-defaults` 会很有帮助。

## 清单文件：`kohaku.yaml`

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

Python 模块通过点号路径解析，比如 `my_pack.tools.my_tool:MyTool`。配置则通过 `@my-pack/creatures/researcher` 这样的路径解析。

如果声明了 `python_dependencies`，`kt install` 会一并安装这些 Python 依赖。

## 安装方式

### Git URL（clone）

```bash
kt install https://github.com/you/my-pack.git
```

会 clone 到 `~/.kohakuterrarium/packages/my-pack/`。更新用 `kt update my-pack`。

### 本地路径（复制）

```bash
kt install ./my-pack
```

会把整个目录复制进去。后续要么重新运行 `kt install`，要么直接改复制过去的那份。

### 本地路径（editable）

```bash
kt install ./my-pack -e
```

这会写入 `~/.kohakuterrarium/packages/my-pack.link`，指向源码目录。你在源码里的修改会立刻生效，不需要重新安装。开发阶段反复调整时很好用。

### 卸载

```bash
kt uninstall my-pack
```

## `@pkg/path` 的解析方式

`@my-pack/creatures/researcher` 会这样解析：

- 如果存在 `my-pack.link`，就跟着这个指针走。
- 否则就解析到 `~/.kohakuterrarium/packages/my-pack/creatures/researcher/`。

`kt run`、`kt terrarium run`、`kt edit`、`kt update`、`base_config:` 继承，以及代码里的 `Agent.from_path(...)` 都会用到这套规则。

## 发现与查看命令

```bash
kt list                         # installed packages + local agents
kt info path/or/@pkg/creature   # details of one config
kt extension list               # all tools/plugins/presets from all packages
kt extension info my-pack       # package metadata + what it ships
```

想快速看当前环境里都有哪些扩展，最方便的就是 `kt extension list`。

## 编辑已安装的配置

```bash
kt edit @my-pack/creatures/researcher
```

这会在 `$EDITOR` 里打开 `config.yaml`，如果没设置，就依次回退到 `$VISUAL` 和 `nano`。editable 安装会直接改源码；普通安装改的是 `~/.kohakuterrarium/packages/` 下面那份副本。

## 发布

1. 把仓库推到 git 上。GitHub、GitLab、自建仓库都可以，只要 `git clone` 能处理就行。
2. 打一个版本标签：`git tag v0.1.0 && git push --tags`。
3. 每次发布时，同步更新 `kohaku.yaml` 里的 `version:`。
4. 把 URL 发出去：`kt install https://your/repo.git`。

这里没有中心注册表。所谓 package，就是一个带 `kohaku.yaml` 的 git 仓库。

### 版本管理

`version:` 最好和 git tag 保持一致。`kt update` 底层做的是 `git pull`；如果使用方固定在某个 tag，上游也可以手动切过去：

```bash
cd ~/.kohakuterrarium/packages/my-pack
git checkout v0.1.0
```

## 运行时的扩展发现

框架加载 creature 时，会先在 creature 本地配置里查找 tool 和 plugin 名称，再去已安装 package 的清单里查。package 里声明的 tool 会通过配置中的 `type: package` 暴露出来：

```yaml
tools:
  - name: my_tool
    type: package          # resolved through the `tools:` list in kohaku.yaml
```

这意味着，一个 package 里的 creature 可以引用另一个 package 里声明的 tool，只要这两个 package 都已经安装。

## 排错

- **`@my-pack/...` 无法解析。** 先用 `kt list` 确认 package 已安装。editable 安装的话，再检查 `.link` 文件指向的目录是否存在。
- **`kt update my-pack` 显示 "skipped"。** editable 安装和非 git package 都不能通过 `kt update` 更新。前者直接改源码，后者重新安装。
- **`python_dependencies` 没有安装。** 确认 `kt install` 在当前环境里有权限安装包，比如使用 virtualenv，或者用 `pip install --user`。
- **package tool 遮蔽了内置 tool。** 内置 tool 的解析优先级更高。如果你想让自己的 tool 生效，改个名字。

## 另见

- [Creatures](/guides/creatures.md)（英文）—— 如何把 creature 打包出去。
- [Custom Modules](/guides/custom-modules.md)（英文）—— 如何编写要随 package 一起发布的 tools 和 plugins。
- [Reference / CLI](/reference/cli.md)（英文）—— `kt install`、`kt list`、`kt extension`。
- [`kt-defaults`](https://github.com/Kohaku-Lab/kt-defaults)（英文）—— 参考 package。
