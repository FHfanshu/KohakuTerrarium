# 安装与快速开始

从零开始，把 KohakuTerrarium 跑起来。

## 1. 装环境

你需要这些：

| 依赖 | 版本 | 怎么检查 | 怎么装 |
|------|------|----------|--------|
| Python | 3.10+ | `python --version` | [python.org](https://python.org) 下载安装包，或用 [Anaconda](https://anaconda.com) |
| git | 任意常见版本都可以 | `git --version` | [git-scm.com](https://git-scm.com) 下载 |
| uv | 建议装，装包更快 | `uv --version` | `pip install uv` 或去 [astral.sh/uv](https://astral.sh/uv) |
| Node.js | 只有 WebUI/桌面端才需要 | `node --version` | [nodejs.org](https://nodejs.org) 下载 LTS 版 |

> Python 3.13 有些依赖可能不兼容，建议用 3.10-3.12。

### Windows 用户注意

装完 Python 后，检查一下这个命令能不能用：

```powershell
python --version
```

如果显示 `'python' 不是内部或外部命令`，说明 PATH 没配好。两个办法：

1. **重装 Python 时勾选 "Add Python to PATH"**
2. **手动加 PATH**：
   ```powershell
   # 找到 Python 安装位置，一般是：
   $env:PATH += ";C:\Users\你的用户名\AppData\Local\Programs\Python\Python310"
   ```

### uv 是什么？

uv 是一个很快的 Python 包管理器。不装也能继续用 pip，但装上之后体验会更好。

一条命令就能装：

```powershell
pip install uv
```

## 2. 装 KohakuTerrarium

### 从源码装（推荐给开发者）

```powershell
git clone https://github.com/Kohaku-Lab/KohakuTerrarium.git
cd KohakuTerrarium
uv pip install -e ".[dev]"
```

看到 `Successfully installed kohakuterrarium-x.x.x` 基本就说明装好了。

如果要跑 WebUI 或桌面端，再加一步：

```powershell
npm install --prefix src/kohakuterrarium-frontend
npm run build --prefix src/kohakuterrarium-frontend
```

### 从 PyPI 装（普通用户推荐）

```powershell
pip install kohakuterrarium
```

同样，看到 `Successfully installed` 基本就可以了。

## 3. 装官方默认 creature 包

**这一步别跳过。** 后面用到的默认 `swe` 依赖它，文档里提到的 `swe_bio_agent` 也是在它的基础上做的本地扩展示例。

```powershell
kt install https://github.com/Kohaku-Lab/kt-defaults.git
```

装完你能用这些：

| creature | 干什么用 |
|----------|----------|
| `@kt-defaults/creatures/general` | 通用助手 |
| `@kt-defaults/creatures/swe` | 软件工程智能体 |
| `@kt-defaults/creatures/reviewer` | 代码审查 |
| `@kt-defaults/terrariums/swe_team` | 多智能体团队 |

## 4. 登录模型

### 最省事的方式：Codex OAuth

```powershell
kt login codex
kt model default gpt-5.4
```

浏览器会弹出来。授权完成后，看到 `Login successful` 就可以了。

### 用其他 OpenAI 兼容的供应商

```powershell
kt login openai --api-key YOUR_API_KEY --base-url https://api.example.com/v1
kt model default gpt-5.4
```

> 具体怎么配模型和预设，看[模型与预设配置](llm-profiles)。

## 5. 先跑默认 `swe`

> 确保你在装好 `kt-defaults` 的目录下执行。

```powershell
kt run @kt-defaults/creatures/swe --mode cli
```

看到下面这样的输出，基本就说明成功了：

```
Loading creature: @kt-defaults/creatures/swe
Connecting to model: gpt-5.4
Ready. Type your message (Ctrl+C to exit):
> 
```

如果你更喜欢全屏界面：

```powershell
kt run @kt-defaults/creatures/swe --mode tui
```

## 6. 可选：跑本地扩展示例 `swe_bio_agent`

> 这一步是可选的。
>
> `swe_bio_agent` 不是官方远端仓库当前默认自带示例，而是一个本地扩展示例。只有当你的工作区里确实有 `examples/agent-apps/swe_bio_agent` 时，下面这些命令才成立。
>
> 如果没有这个目录，请跳过本节，继续使用默认 `@kt-defaults/creatures/swe`。

```powershell
kt run examples/agent-apps/swe_bio_agent --mode cli
```

它比默认 `swe` 多了两样东西：

- **硬约束**：不先读完仓库规则文件，就不能改代码
- **审计留痕**：所有操作都会写入 JSONL 日志，方便事后复盘

## 7. 验证安装

按顺序确认：

```powershell
# 1. 确认 creature 能被识别
kt info @kt-defaults/creatures/swe

# 2. 跑一下默认 SWE
kt run @kt-defaults/creatures/swe --mode cli

# 3. 检查 session 文件有没有生成
dir ~/.kohakuterrarium/sessions/*.kohakutr
```

都没问题的话，基础安装就完成了。

如果你本地也有 `examples/agent-apps/swe_bio_agent`，可以额外验证：

```powershell
kt info examples/agent-apps/swe_bio_agent
kt run examples/agent-apps/swe_bio_agent --mode cli
dir examples/agent-apps/swe_bio_agent/artifacts/audit/
```

## 经常遇到的问题

### `kt: command not found`

Python Scripts 目录没加到 PATH 里。这样修：

```powershell
# 找到安装位置
python -m site --user-base

# 临时加到 PATH
$env:PATH += ";$(python -m site --user-base)\Scripts"
```

### `kt install` 超时或失败

大概率是网络问题。可以按下面几种方式排查：

1. 确认 git 装了：`git --version`
2. 网络受限的话用代理
3. 或者手动克隆再本地装：

```powershell
git clone https://github.com/Kohaku-Lab/kt-defaults.git
kt install ./kt-defaults
```

### `kt login codex` 没弹浏览器

手动复制终端里显示的 URL 到浏览器里打开就行。

### 模型调用失败

```powershell
# 查看当前模型配置
kt model show

# 列出可用模型
kt model list

# 重新设置
kt model default gpt-5.4
```

### 找不到 session 文件

session 默认保存在 `~/.kohakuterrarium/sessions/`。也可以用 `kt resume --list` 查看所有 session。

---

[CLI 与 WebUI 使用 →](cli-webui)