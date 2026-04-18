# 第一个 Creature

你已经装好了 KohakuTerrarium，现在想从零开始，做出一个自己能看懂、也能直接跑起来的定制 creature。

这篇做完，你会：跑一个现成 creature、恢复一次 session、把它 fork 到自己的目录、改 system prompt、加一个工具，再跑一遍。

前提是：你的 `PATH` 里已经有 `kt`（可以在仓库里执行 `uv pip install -e .`，或者直接安装发布版），机器也能访问 API。

creature 本质上就是一个独立 agent：controller + input + output + tools，也可以再带 triggers、sub-agents、plugins。这篇教程走最短的一条路，把这些东西都过一遍。

## 第 1 步：安装默认包

先把自带的 creatures（`swe`、`general`、`reviewer`、`root` ……）装到本机，这样后面就能用 `@kt-defaults/...` 来引用。

```bash
kt install https://github.com/Kohaku-Lab/kt-defaults.git
```

`kt install` 可以接 git URL，也可以接本地路径。装完以后，包会放在 `~/.kohakuterrarium/packages/kt-defaults/`，配置里就能直接写 `@kt-defaults/...`。

可以检查一下：

```bash
kt list
```

你应该会看到 `kt-defaults`，还有里面那些 creatures：`swe`、`general`、`reviewer`、`root`、`researcher`、`ops`、`creative`。

## 第 2 步：登录 LLM

选一个 provider，然后把登录弄好。SWE creature 用默认模型，所以你得先把凭据配上。

如果你有 ChatGPT 订阅，想走 OAuth：

```bash
kt login codex
```

不然就给别的 backend 配 key，比如 OpenAI、Anthropic、OpenRouter：

```bash
kt config key set openai
```

你也可以顺手设一个默认模型 preset，这样以后每次都不用再传 `--llm`：

```bash
kt model list
kt model default gpt-5.4
```

## 第 3 步：先跑一个现成 creature

先看一遍完整 creature 是怎么工作的，再动手改。

```bash
kt run @kt-defaults/creatures/swe --mode cli
```

给它一个简单请求：

```text
> list the python files in this directory
```

它会一边输出答案，一边调用工具（`glob`、`read`），最后把结果显示出来。用 `/exit` 或 Ctrl+C 退出。退出时，`kt` 会打印一个 resume 提示，格式大概像 `kt resume <session-name>`；session 会自动保存到 `~/.kohakuterrarium/sessions/*.kohakutr`。

## 第 4 步：恢复 session

这一步就是确认：session 会保存，而且能接着聊。

```bash
kt resume --last
```

这会恢复最近一次 session。你会回到刚才那段对话里，scratchpad、工具历史和模型也都还是原来的。看完再退出一次就行。

## 第 5 步：把 creature fork 到本地目录

现在做一个你自己维护、但又是基于 SWE 的 creature。

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

`base_config` 会把 SWE creature 里的东西带过来：LLM 默认值、工具集、sub-agents，还有上游的 system prompt。你自己的 `system.md` 会接在继承来的 prompt 后面；prompt 会沿着继承链一路拼起来。别的没显式设置的部分，都会继续继承。

## 第 6 步：加一个工具

接下来在继承来的工具列表里再加一项。这里用 `web_search`。

编辑 `creatures/my-swe/config.yaml`：

```yaml
name: my_swe
version: "1.0"
base_config: "@kt-defaults/creatures/swe"

system_prompt_file: prompts/system.md

tools:
  - { name: web_search, type: builtin }
```

像 `tools:`、`subagents:` 这种列表，默认会在继承列表的基础上继续加，按 `name` 去重；除非你用 `no_inherit:` 把继承关掉。所以这里只是把 `web_search` 塞进 SWE 原来的工具集，不用把其他条目再写一遍。

## 第 7 步：运行你自己的 creature

```bash
kt run creatures/my-swe --mode cli
```

给它一个需要联网的问题：

```text
> search the web for "kohakuterrarium github" and summarise the top result
```

这时候你会看到，system prompt 里的 house rules 已经生效了，新加的 `web_search` 也能用了。正常退出就行，session 还是会自动保存。

## 你学到了什么

- creature 不是 prompt，它是一个带配置的文件夹。
- 开箱即用的基本流程就是 `kt install`、`kt login`、`kt run`。
- `kt resume` 可以把完整 session 从磁盘拉回来。
- `base_config: "@pkg/creatures/<name>"` 会继承全部内容；标量字段直接覆盖，`tools:` / `subagents:` 则是在原有基础上扩展。
- `system_prompt_file` 会沿着继承链拼接。

## 接下来可以看什么

- [Creatures](../guides/creatures.md) —— 按实际使用场景解释各个配置字段。
- [Configuration reference](../guides/configuration.md) —— 完整 schema 和继承规则。
- [First custom tool](first-custom-tool.md) —— `builtin` 不够用的时候怎么做。
- [What is an agent](../concepts/foundations/what-is-an-agent.md) —— 理解配置为什么会长这样。