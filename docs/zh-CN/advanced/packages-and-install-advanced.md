# kt install 与 package 进阶

这篇文档面向需要分享 creatures、terrariums、工具或插件的用户。

KohakuTerrarium 的 package 是一个带有 `kohaku.yaml` 清单文件的目录。它可以包含 creatures、terrariums、自定义工具、插件和 LLM 预设。`kt install` 会把它安装到 `~/.kohakuterrarium/packages/<name>/`，然后用 `@<name>/path` 语法引用里面的内容。

概念入门：[边界](./concepts/boundaries.md) —— package 是框架让"分享可复用组件"变得低成本的方式。

## 官方包：`kt-biome`

大多数人第一个安装的包是 `kt-biome` —— 这是一个示例包，包含 `swe`、`reviewer`、`researcher`、`ops`、`creative`、`general`、`root` 这些 creatures，还有 `swe_team` 和 `deep_research` 这些 terrariums，以及一些插件。

```bash
kt install https://github.com/Kohaku-Lab/kt-biome.git
kt run @kt-biome/creatures/swe
```

当你自己构建包时，可以参考 `kt-biome` 的结构。

## 清单文件：`kohaku.yaml`

```yaml
name: my-pack
version: "0.1.0"
description: "我的共享智能体组件"

creatures:
  - name: researcher           # 目录在 creatures/researcher/

terrariums:
  - name: research_team        # 目录在 terrariums/research_team/

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
  my_pack/                     # 可安装的 Python 包
    __init__.py
    tools/my_tool.py
    plugins/my_guard.py
```

Python 模块通过点分隔路径解析（`my_pack.tools.my_tool:MyTool`）。配置通过 `@my-pack/creatures/researcher` 解析。

如果声明了 `python_dependencies`，`kt install` 时会自动安装这些依赖。

## 安装模式

### Git URL（克隆）

```bash
kt install https://github.com/you/my-pack.git
```

克隆到 `~/.kohakuterrarium/packages/my-pack/`。用 `kt update my-pack` 更新。

### 本地路径（复制）

```bash
kt install ./my-pack
```

复制文件夹进去。更新需要重新运行 `kt install` 或直接编辑副本。

### 本地路径（可编辑）

```bash
kt install ./my-pack -e
```

在 `~/.kohakuterrarium/packages/my-pack.link` 写一个指向源目录的链接。源目录的修改会立即生效 —— 不需要重新安装。适合开发时迭代。

### 卸载

```bash
kt uninstall my-pack
```

## 解析 `@pkg/path`

`@my-pack/creatures/researcher` 的解析规则：

- 如果存在 `my-pack.link`：跟随指针指向的目录。
- 否则：`~/.kohakuterrarium/packages/my-pack/creatures/researcher/`。

`kt run`、`kt terrarium run`、`kt edit`、`kt update`、`base_config:` 继承，以及编程式的 `Agent.from_path(...)` 都使用这个路径。

## 查询命令

```bash
kt list                         # 已安装的包 + 本地智能体
kt info path/or/@pkg/creature   # 查看某个配置的详情
kt extension list               # 列出所有包提供的工具/插件/预设
kt extension info my-pack       # 查看包元数据 + 包含内容
```

`kt extension list` 是查看已安装包中所有可用内容的最简单方式。

## 编辑已安装的配置

```bash
kt edit @my-pack/creatures/researcher
```

在 `$EDITOR` 中打开 `config.yaml`（回退到 `$VISUAL`，然后是 `nano`）。对于可编辑安装，这会编辑源目录；对于普通安装，编辑的是 `~/.kohakuterrarium/packages/` 下的副本。

## 发布

1. 把仓库推送到 git（GitHub、GitLab、自托管 —— 任何 `git clone` 能处理的都行）。
2. 打标签：`git tag v0.1.0 && git push --tags`。
3. 每次发布时更新 `kohaku.yaml` 里的 `version:`。
4. 分享 URL：`kt install https://your/repo.git`。

没有中心化注册表。包就是带有 `kohaku.yaml` 的 git 仓库。

### 版本管理

保持 `version:` 和 git 标签同步。`kt update` 底层执行 `git pull`；固定到某个标签的用户可以手动切换：

```bash
cd ~/.kohakuterrarium/packages/my-pack
git checkout v0.1.0
```

## 运行时扩展发现

当框架加载一个 creature 时，加载器会先在 creature 的本地配置里查找工具/插件名称，然后在已安装包的清单里查找。包声明的工具在配置里通过 `type: package` 引用：

```yaml
tools:
  - name: my_tool
    type: package          # 通过 kohaku.yaml 里的 tools: 列表解析
```

这样，一个包里的 creature 可以引用另一个包里声明的工具，只要两个包都安装了就行。

## 排错

- **`@my-pack/...` 解析失败。** 运行 `kt list` 确认包已安装。对于可编辑安装，检查 `.link` 文件指向的目录是否存在。
- **`kt update my-pack` 提示 "skipped"。** 可编辑安装和非 git 包不能用 `kt update` 更新。编辑源目录（可编辑）或重新安装（复制）。
- **`python_dependencies` 没安装。** 确认 `kt install` 有权限在当前环境安装包（使用虚拟环境或 `pip install --user`）。
- **包工具覆盖了内置工具。** 内置工具优先解析。如果你想让包工具优先，重命名包工具。

## 参考

- [Packages 指南](./packages.md)
- [Creatures](configuration.md) —— 打包一个 creature
- [自定义模块](custom-modules.md) —— 编写要发布的工具/插件
- [CLI 参考](./reference/cli.md) —— `kt install`、`kt list`、`kt extension`
- [`kt-biome`](https://github.com/Kohaku-Lab/kt-biome) —— 参考包