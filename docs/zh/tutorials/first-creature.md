# 第一个 Creature

**问题：** 你已经装好 KohakuTerrarium，现在想从零开始，做出一个自己能看懂、能直接运行的定制 creature。

**完成后：** 你会跑起一个现成 creature，恢复一次 session，把它 fork 到自己的目录里，改掉 system prompt，加一个工具，再跑一遍。

**前提：** 你的 `PATH` 里有 `kt`（在仓库里执行 `uv pip install -e .`，或直接安装已发布版本），并且这台机器能访问 API。

creature 是一个独立 agent：controller + input + output + tools（也可以再带 triggers、sub-agents、plugins）。这篇教程走最短路径，把这些部件都碰一遍。

## 第 1 步：安装默认包

目标：先把自带的 creatures（`swe`、`general`、`reviewer`、`root` ……）装到本机，这样后面就能用 `@kt-defaults/...` 引用它们。

```bash
kt install https://github.com/Kohaku-Lab/kt-defaults.git
```

`kt install` 可以接 git URL，也可以接本地路径。装完后，包会在 `~/.kohakuterrarium/packages/kt-defaults/`，配置里可以用 `@kt-defaults/...` 引用。

检查一下：

```bash
kt list
```

你应该能看到 `kt-defaults`，以及里面的 creatures：`swe`、`general`、`reviewer`、`root`、`researcher`、`ops`、`creative`。

## 第 2 步：登录 LLM

目标：选一个 provider 并完成登录。SWE creature 用的是默认模型，所以你得先给它配好凭据。

如果你有 ChatGPT 订阅，想用 OAuth：

```bash
kt login codex
```

不然就给别的 backend 配 key，比如 OpenAI、Anthropic、OpenRouter：

```bash
kt config key set openai
```

你也可以设一个默认模型 preset，这样每次就不用再手动传 `--llm`：

```bash
kt model list
kt model default gpt-5.4
```

## 第 3 步：先跑一个现成 creature

目标：先看一遍完整 creature 的运行方式，再开始改。

```bash
kt run @kt-defaults/creatures/swe --mode cli
```

给它一个简单请求：

```text
> list the python files in this directory
```

它会流式输出答案，调用工具（`glob`、`read`），然后把结果显示出来。用 `/exit` 或 Ctrl+C 退出。退出时，`kt` 会打印一个 resume 提示，格式大概像 `kt resume <session-name>`；session 会自动保存到 `~/.kohakuterrarium/sessions/*.kohakutr`。

## 第 4 步：恢复 session

目标：确认 session 会持久化，也能恢复。

```bash
kt resume --last
```

这会恢复最近一次 session。你会回到同一段对话里，scratchpad、工具历史和模型也都还是原来的。看完后再退出一次。

## 第 5 步：把 creature fork 到本地目录

目标：做一个归你自己维护、并且基于 SWE 的 creature。

```bash
mkdir -p creatures/my-swe/prompts
```

`creatures/my-swe/config.yaml`：

```yaml
name: my_swe
version: "1.0"
base_config: "@kt-defaults/creatures/swe"

system_prompt_file: prompts/system.md
```

`creatures/my-swe/prompts/system.md`：

```markdown
# My SWE

You are a careful repo-surgery agent.

House rules:
- read before editing, always
- keep diffs small and obvious
- when unsure, ask rather than guess
```

`base_config` 会把 SWE creature 里的东西都带过来：LLM 默认值、工具集、sub-agents，还有上游 system prompt。你的 `system.md` 会追加到继承来的 prompt 后面（prompt 会沿继承链拼接）。其他没显式设置的部分都会继续继承。

## 第 6 步：加一个工具

目标：在继承来的工具列表上再加一项。这里加 `web_search`，平时很实用。

编辑 `creatures/my-swe/config.yaml`：

```yaml
name: my_swe
version: "1.0"
base_config: "@kt-defaults/creatures/swe"

system_prompt_file: prompts/system.md

tools:
  - { name: web_search, type: builtin }
```

像 `tools:`、`subagents:` 这样的列表，默认会在继承列表的基础上继续追加（按 `name` 去重），除非你用 `no_inherit:` 关掉继承。所以这里会把 `web_search` 加进 SWE 的工具集，不需要把其他条目再写一遍。

## 第 7 步：运行你自己的 creature

```bash
kt run creatures/my-swe --mode cli
```

给它一个需要联网的问题：

```text
> search the web for "kohakuterrarium github" and summarise the top result
```

你会看到 system prompt 里的 house rules 生效了，新加的 `web_search` 工具也能用了。正常退出就行；session 会自动保存。

## 你学到了什么

- creature 不是 prompt；它是一个**带配置的文件夹**。
- 开箱即用的基本流程就是 `kt install` + `kt login` + `kt run`。
- `kt resume` 可以从磁盘恢复完整 session。
- `base_config: "@pkg/creatures/<name>"` 会继承全部内容；标量字段会覆盖，`tools:` / `subagents:` 会扩展。
- `system_prompt_file` 会沿继承链拼接。

## 接下来可以读什么

- [Creatures](/guides/creatures.md)（英文）—— 按上下文解释各个配置字段。
- [Configuration reference](/guides/configuration.md)（英文）—— 完整 schema 和继承规则。
- [First custom tool](/tutorials/first-custom-tool.md)（英文）—— 当 `builtin` 不够用时怎么做。
- [What is an agent](/concepts/foundations/what-is-an-agent.md)（英文）—— 为什么配置会长这个样子。