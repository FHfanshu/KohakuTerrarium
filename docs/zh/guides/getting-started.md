# 快速开始

从没跑过 KohakuTerrarium？几分钟内在本机跑一个 agent。

框架本身是核心，外加可安装的 creature/plugin 包。官方包 `kt-defaults` 有现成的 SWE agent、reviewer、researcher 和几个 terrarium。不用写代码就能试。

概念：[什么是 creature](../concepts/foundations/what-is-an-agent.md)、[为什么用这个框架](../concepts/foundations/why-kohakuterrarium.md)。

## 1. 安装

PyPI（推荐）：
```bash
pip install kohakuterrarium
# 或带更多可选依赖（语音、embedding等）
pip install "kohakuterrarium[full]"
```

装完有 `kt` 命令。验证：
```bash
kt --version
```

源码装（开发用）：
```bash
git clone https://github.com/Kohaku-Lab/KohakuTerrarium.git
cd KohakuTerrarium
uv pip install -e ".[dev]"
```

要跑 `kt web` 或 `kt app`，先构建前端：
```bash
npm install --prefix src/kohakuterrarium-frontend
npm run build --prefix src/kohakuterrarium-frontend
```

不构建的话，`kt web` 只打印提示，`kt app` 打不开。

## 2. 装默认 creature 包

`kt-defaults` 包含 OOTB creatures（`swe`、`reviewer`、`researcher`、`ops`、`creative`、`general`、`root`) 和几个 terrarium。

```bash
kt install https://github.com/Kohaku-Lab/kt-defaults.git
kt list
```

装后包在 `~/.kohakuterrarium/packages/<name>/`，用 `@<package>/path` 引用。

## 3. 认证模型供应商

选一个：

**Codex（ChatGPT订阅，不用API key）**
```bash
kt login codex
kt model default gpt-5.4
```

浏览器打开，完成 device-code 流，token 存到 `~/.kohakuterrarium/codex-auth.json`。

**OpenAI兼容供应商（API key）**
```bash
kt config key set openai          # 输入 key
kt config llm add                 # 交互式构建 preset
kt model default <preset-name>
```

**其他供应商**：`anthropic`、`openrouter`、`gemini` 等是内置 backend。见 `kt config provider list` 和[配置](configuration.md)。

## 4. 跑 creature

```bash
kt run @kt-defaults/creatures/swe --mode cli
```

进入交互式 SWE agent。输入请求，它用 shell、文件、编辑工具在当前工作目录操作。Ctrl+C 退出并打印 resume 提示。

模式：
- `cli` — Rich inline（TTY默认）
- `tui` — 全屏 Textual app
- `plain` — 纯 stdout/stdin，管道或 CI 用

单次运行指定模型：
```bash
kt run @kt-defaults/creatures/swe --llm claude-opus-4.6
```

## 5. Resume

session 自动存到 `~/.kohakuterrarium/sessions/*.kohakutr`（除非 `--no-session`）。恢复：
```bash
kt resume --last                # 最近
kt resume                       # 交互选择
kt resume swe_20240101_1234     # 按名前缀
```

agent 从保存配置重建，重放对话，重注册 trigger，恢复 scratchpad 和 channel 历史。见[Sessions](/guides/sessions.md)（英文）。

## 6. 搜索 session 历史

session 存了操作记录，可当小型本地知识库搜索：
```bash
kt embedding ~/.kohakuterrarium/sessions/<name>.kohakutr
kt search <name> "auth bug"
```

完整流程见[Memory](memory.md)。

## 7. Web UI 或桌面应用

```bash
kt web           # 本地 http://127.0.0.1:8001
kt app           # 原生桌面窗口（需 pywebview）
```

daemon 模式：
```bash
kt serve start
kt serve status
kt serve logs --follow
kt serve stop
```

见[Serving](serving.md)。

## 排错

**`kt login codex` 没开浏览器：** 复制 CLI 打印的 URL，手动在浏览器打开。回调端口占用时先释放。

**`kt web` 404：** 前端没构建。跑 `npm install --prefix src/kohakuterrarium-frontend && npm run build --prefix src/kohakuterrarium-frontend`。PyPI 安装已带构建产物。

**`~/.kohakuterrarium/` 权限错误：** 框架首次运行创建该目录。如果已存在但属主是其他用户（常见于 `sudo pip install`），修正：`chown -R $USER ~/.kohakuterrarium`。

**`kt run` 报 "no model set"：** 跳了第3步。跑 `kt model default <name>` 或传 `--llm <name>`。

**`ModuleNotFoundError: pywebview`：** `kt app` 需桌面依赖：`pip install 'kohakuterrarium[full]'`（或用 `kt web`）。

## 参考

- [Creatures](creatures.md) 如何继承或定制 OOTB agents。
- [Sessions](sessions.md) resume 语义和 compaction。
- [Serving](serving.md) `kt web`、`kt app`、`kt serve` 选择。
- [CLI 参考](../reference/cli.md) 所有命令和参数。