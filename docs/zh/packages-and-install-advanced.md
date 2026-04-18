# kt install 与 package 进阶

`kt install` 安装的是 package，不是 skill。

## package 是什么

带 `kohaku.yaml` 的目录。可以包含：creatures、terrariums、tools、plugins、LLM presets。

分发和复用单位，不是"模型怎么理解工具"。

## kt install 做什么

git URL 就 clone，本地目录就复制，`-e` 就做可编辑链接。装到 `~/.kohakuterrarium/packages/<name>/`。

装完用 `@pkg/path` 引用：
```bash
kt install https://github.com/Kohaku-Lab/kt-defaults.git
kt run @kt-defaults/creatures/swe
```

## @pkg/path 是什么

包内资源路径。不是 skill 名，不是 MCP server 名，不是 Python 模块路径。就是装完后定位 creature/terrarium 的路径。

## 为什么不是 skill

package 是分发单位，tool 是能力单位，skill 是文档单位。三层不一样。package 可能带来新 tool 和文档，但不等于 package 本身是 skill。

## 什么时候用 package

复用别人的 creature、发团队模板、共享 plugin/tool/preset、让 base_config 继承基座。

`kt-defaults` 就是默认内容集合，不是"skill 包"。

## 可编辑安装

开发时用 `-e`：
```bash
kt install ./my-pack -e
```
写 `.link` 指向源目录，改源码不用重装。

## 示例

结构：
```text
my-pack/
  kohaku.yaml
  creatures/
    helper/
      config.yaml
```

kohaku.yaml：
```yaml
name: my-pack
version: "0.1.0"
creatures:
  - name: helper
```

装：
```bash
kt install ./my-pack -e
```

跑：
```bash
kt run @my-pack/creatures/helper
```

## 边界

package：把内容发给别人
MCP：把外部能力接进来

package：内容分发
skills：工具说明文档

package 可以带 MCP 配置、带 tool 文档，但不等于它就是 MCP 或 skill。

## 参考

- [英文 Packages 指南](../guides/packages.md)
- [配置写法](configuration)
- [skills 进阶](skills-and-skill-mode-advanced)