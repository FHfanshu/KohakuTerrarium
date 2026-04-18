# 快速开始

如果你还没跑过 KohakuTerrarium，照着这篇做，几分钟就能在自己机器上跑起一个 agent。

KohakuTerrarium 本体是核心框架，另外还支持安装可复用的 creature/plugin 包。官方包 `kt-defaults` 里已经带了现成的 SWE agent、reviewer、researcher，还有几个 terrarium。想试用的话，不用先自己写东西。

先补两个概念：[什么是 creature](../concepts/foundations/what-is-an-agent.md)、[为什么用这个框架](../concepts/foundations/why-kohakuterrarium.md)。

## 1. 安装

### 从 PyPI 安装（推荐）

```bash
pip install kohakuterrarium
# 或者安装更多可选依赖（语音、embedding 等）
pip install "kohakuterrarium[full]"
```

装好以后会有 `kt` 命令。先确认一下：

```bash
kt --version
```

### 从源码安装（开发用）

```bash
git clone https://github.com/Kohaku-Lab/KohakuTerrarium.git
cd KohakuTerrarium
uv pip install -e ".[dev]"
```

如果你想用 `kt web` 或 `kt app` 提供前端界面，前端要先构建一次：

```bash
npm install --prefix src/kohakuterrarium-frontend
npm run build --prefix src/kohakuterrarium-frontend
```

不做这一步的话，`kt web` 只会打印提示信息，`kt app` 也打不开。

## 2. 安装默认 creature 包

`kt-defaults` 里有开箱即用的 creatures：`swe`、`reviewer`、`researcher`、`ops`、`creative`、`general`、`root`，还带几个 terrariums。

```bash
kt install https://github.com/Kohaku-Lab/kt-defaults.git
kt list
```

安装好的包会放在 `~/.kohakuterrarium/packages/<name>/` 下，引用时用 `@<package>/path` 这种写法。

## 3. 认证模型提供方

选一种就行。

**Codex（有 ChatGPT 订阅，不用 API key）**
```bash
kt login codex
kt model default gpt-5.4
```

命令会打开浏览器。完成 device-code 流程后，token 会存到 `~/.kohakuterrarium/codex-auth.json`。

**OpenAI 兼容提供方（用 API key）**
```bash
kt config key set openai          # 会提示你输入 key
kt config llm add                 # 交互式创建 preset
kt model default <preset-name>
```

**其他提供方**：`anthropic`、`openrouter`、`gemini` 等都内置支持。具体可以看 `kt config provider list` 和[配置](configuration.md)。

## 4. 运行一个 creature

```bash
kt run @kt-defaults/creatures/swe --mode cli
```

运行后会进入 SWE agent 的交互界面。你输入请求，它会在当前工作目录里调用 shell、文件和编辑工具。按 Ctrl+C 可以正常退出，CLI 还会顺手给你一条 resume 提示。

可选模式：

- `cli` — Rich 行内界面（TTY 下默认）
- `tui` — 全屏 Textual 应用
- `plain` — 纯 stdout/stdin，适合管道或 CI

如果只想这一次换个模型，可以这样：

```bash
kt run @kt-defaults/creatures/swe --llm claude-opus-4.6
```

## 5. 恢复 session

session 会自动保存到 `~/.kohakuterrarium/sessions/*.kohakutr`，除非你传了 `--no-session`。要恢复的话：

```bash
kt resume --last                # 最近一次
kt resume                       # 交互式选择
kt resume swe_20240101_1234     # 按名称前缀恢复
```

agent 会按保存时的配置重新建起来，重放对话，重新注册可恢复的 triggers，再把 scratchpad 和 channel 历史一并恢复。完整说明见[Sessions](sessions.md)。

## 6. 搜索 session 历史

因为 session 保存的是操作过程，你也可以把它当成一个小型本地知识库来查：

```bash
kt embedding ~/.kohakuterrarium/sessions/<name>.kohakutr
kt search <name> "auth bug"
```

完整流程见[Memory](memory.md)。

## 7. 打开 Web UI 或桌面应用

```bash
kt web           # 本地 Web 服务，地址是 http://127.0.0.1:8001
kt app           # 原生桌面窗口（需要 pywebview）
```

如果你想让服务在终端退出后继续跑，可以用 daemon：

```bash
kt serve start
kt serve status
kt serve logs --follow
kt serve stop
```

什么时候该用哪一种，见[Serving](serving.md)。

## 排错

- **`kt login codex` 没有打开浏览器。** 把 CLI 打印出来的 URL 复制出来，手动贴到浏览器里打开。如果回调端口被占用了，先释放端口再重试。
- **`kt web` 没内容，或者访问 `/` 返回 404。** 前端还没构建。运行 `npm install --prefix src/kohakuterrarium-frontend && npm run build --prefix src/kohakuterrarium-frontend`。如果你是从 PyPI 安装，构建产物本来就已经带上了。
- **往 `~/.kohakuterrarium/` 写入时报 `Permission denied`。** 框架第一次运行时会创建这个目录。如果目录已经存在，但属主是别的用户（常见于 `sudo pip install` 之后），改一下属主：`chown -R $USER ~/.kohakuterrarium`。
- **`kt run` 提示 `no model set`。** 你跳过了第 3 步。先运行 `kt model default <name>`，或者直接传 `--llm <name>`。
- **`ModuleNotFoundError: pywebview`。** `kt app` 需要桌面相关依赖：`pip install 'kohakuterrarium[full]'`。不装也行，改用 `kt web`。

## 另见

- [Creatures](creatures.md)：怎么继承或定制开箱即用的 agents。
- [Sessions](sessions.md)：resume 的语义和 compaction。
- [Serving](serving.md)：`kt web`、`kt app`、`kt serve` 该怎么选。
- [CLI 参考](../reference/cli.md)：所有命令和参数。
