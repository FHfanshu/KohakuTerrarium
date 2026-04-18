# 安装与快速开始

这篇文档会一步一步带你安装 KohakuTerrarium（琥珀生态瓶），并确认它已经可以正常运行。

## 环境

在开始之前，请先确认你的电脑上已经安装了下面这些工具：

| 依赖 | 版本 | 如何检查 | 如何安装 |
|---|---|---|---|
| Python | 3.10+ | `python --version` | [python.org](https://python.org) 或 Anaconda |
| git | 任意 | `git --version` | [git-scm.com](https://git-scm.com) |
| uv | 建议安装 | `uv --version` | `pip install uv` 或 [astral.sh/uv](https://astral.sh/uv) |
| Node.js | 只有使用 WebUI 时才需要 | `node --version` | [nodejs.org](https://nodejs.org) LTS |

注意：Python 3.13 目前和部分依赖库还不完全兼容，因此建议你使用 Python 3.10 到 3.12。

## Windows PATH

如果你在 Windows 上安装完 Python，建议先马上检查一下命令行里能不能直接找到 Python：

```powershell
python --version
```

如果提示 `'python' 不是内部或外部命令`，就说明 Python 没有正确加入 PATH 环境变量。你可以重新安装 Python，并勾选安装界面里的 `Add Python to PATH`；也可以手动把 Python 的安装目录加到 PATH，例如：

```powershell
$env:PATH += ";C:\Users\用户名\AppData\Local\Programs\Python\Python310"
```

## uv

`uv` 是一个速度很快的 Python 包管理工具。你不安装也能继续，KohakuTerrarium 会退回到使用 `pip`；不过如果装了 `uv`，安装依赖通常会快很多，整个过程也会更顺畅。

```powershell
pip install uv
```

## 安装琥珀生态瓶

如果你准备直接从源码安装（更适合开发者或想改代码的人），可以执行下面这几条命令：

```powershell
git clone https://github.com/Kohaku-Lab/KohakuTerrarium.git
cd KohakuTerrarium
uv pip install -e ".[dev]"
```

当你看到 `Successfully installed kohakuterrarium-x.x.x` 之类的输出时，就表示安装已经成功了。

如果你还想使用 WebUI 或桌面端，那么在安装完 Python 依赖之后，还需要继续安装前端依赖并构建前端资源：

```powershell
npm install --prefix src/kohakuterrarium-frontend
npm run build --prefix src/kohakuterrarium-frontend
```

如果你只是普通用户，只想先装好再用，也可以直接从 PyPI 安装：

```powershell
pip install kohakuterrarium
```

## kt-biome 智能体包

`kt-biome` 是官方默认智能体包，包含开箱即用的 creatures（`swe`、`reviewer`、`researcher`、`ops`、`creative`、`general`、`root`）以及几个 terrariums。

这一步建议不要跳过。默认提供的 `swe` creature 依赖这个仓库里的默认资源，只有先安装好它，后面的示例才能正常跑起来。

```powershell
kt install https://github.com/Kohaku-Lab/kt-biome.git
```

安装完成后，包会存放在 `~/.kohakuterrarium/packages/kt-biome/`，你可以用 `@kt-biome/path` 语法引用里面的内容。可用资源如下：

| creature | 用途 |
|----------|------|
| `@kt-biome/creatures/general` | 通用助手 |
| `@kt-biome/creatures/swe` | 软件工程助手 |
| `@kt-biome/creatures/reviewer` | 代码审查助手 |
| `@kt-biome/terrariums/swe_team` | 多智能体协作示例 |

## 登录模型

如果你使用 Codex OAuth（Go 级别以上有效 ChatGPT 订阅），可以执行：

```powershell
kt login codex
kt model default gpt-5.4
```

运行后，系统会自动弹出浏览器窗口。你只要在浏览器里完成授权，终端里看到 `Login successful` 就说明登录已经成功。

如果你使用的是其他兼容 OpenAI 接口的服务商（需要 API key），需要先配置密钥再创建模型预设：

```powershell
kt config key set openai          # 交互式输入密钥
kt config llm add                 # 交互式创建模型预设
kt model default my-model         # 设为默认（my-model 是你刚才创建的预设名）
```

也可以手动编辑 `~/.kohakuterrarium/llm_profiles.yaml`，详见[模型与预设配置](llm-profiles)。

## 运行默认的 swe

安装和登录都完成后，你就可以先运行默认的 `swe` creature 试试看：

```powershell
kt run @kt-biome/creatures/swe --mode cli
```

如果启动成功，你通常会看到类似下面的输出：

```
Loading creature: @kt-biome/creatures/swe
Connecting to model: gpt-5.4
Ready. Type your message (Ctrl+C to exit):
```

如果你更喜欢全屏终端界面，也可以使用 TUI 模式：

```powershell
kt run @kt-biome/creatures/swe --mode tui
```

## 本地扩展示例

如果你的项目里已经有 `examples/agent-apps/swe_bio_agent` 这个示例目录，就可以这样运行它：

```powershell
kt run examples/agent-apps/swe_bio_agent --mode cli
```

这个示例相比默认的 `swe` 多了两个特性：
1. 硬约束机制：要求智能体先读取规则文件，之后才能修改代码。
2. 审计留痕功能：所有操作都会记录到 JSONL 文件里，方便后续追踪。

## 验证

安装完成后，你可以运行下面这些命令，确认环境是否已经配置好：

```powershell
kt --version
kt list
kt info @kt-biome/creatures/swe
dir ~/.kohakuterrarium/sessions/*.kohakutr
```

如果这些命令都能正常输出结果，就说明安装和基础配置已经完成了。

如果你还安装了本地扩展，也可以额外验证一下：

```powershell
kt info examples/agent-apps/swe_bio_agent
dir examples/agent-apps/swe_bio_agent/creatures/swe_bio_agent/artifacts/audit/*.jsonl
```

## 常见问题

如果系统提示找不到 `kt` 命令，通常说明 PATH 环境变量没有配置好。Windows 用户可以先执行下面这条命令，把用户级 Python 脚本目录加入 PATH：

```powershell
$env:PATH += ";$(python -m site --user-base)\Scripts"
```

如果 `kt install` 命令执行超时，通常是网络连接有问题。请先确认 `git` 已经安装好，然后再尝试配置网络代理，或者手动 `clone` 仓库后再安装。

如果登录失败，请依次检查下面几项：API key 是否正确、base URL 是否填写正确、模型名称是否填写正确。

如果你找不到 session 文件，默认存储路径是 `~/.kohakuterrarium/sessions/`。你也可以运行 `kt resume --list`，查看所有历史会话。