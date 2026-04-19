# 安装与快速开始

装 KohakuTerrarium，跑起来。

## 环境

| 依赖 | 版本 | 检查安装 | 去哪里安装 |
|------|------|----|----|
| Python | 3.10+ | `python --version` | [python.org](https://python.org) 或 Anaconda |
| git | 任意 | `git --version` | [git-scm.com](https://git-scm.com) |
| uv | 建议装 | `uv --version` | `pip install uv` 或 [astral.sh/uv](https://astral.sh/uv) |
| Node.js | WebUI需要 | `node --version` | [nodejs.org](https://nodejs.org) LTS |


## Windows PATH

装完 Python 检查：
```powershell
python --version
```

报错 `'python' 不是内部或外部命令` 说明 PATH 没配好。重装勾选 "Add Python to PATH" 或手动加：
```powershell
$env:PATH += ";C:\Users\用户名\AppData\Local\Programs\Python\Python310"
```

## uv

快的包管理器。不装也能用 pip，装了体验更好。
```powershell
pip install uv
```

## 装 KohakuTerrarium

强烈建议在虚拟环境里装，或者加 `--user` 参数，不然容易污染系统环境或报权限错。

建虚拟环境并激活（推荐）：
```powershell
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

源码装（开发者）：
```powershell
git clone https://github.com/Kohaku-Lab/KohakuTerrarium.git
cd KohakuTerrarium
uv pip install -e ".[dev]"
```

看到 `Successfully installed kohakuterrarium-x.x.x` 就装好了。

WebUI/桌面端再加：
```powershell
npm install --prefix src/kohakuterrarium-frontend
npm run build --prefix src/kohakuterrarium-frontend
```

PyPI 装（普通用户）：
```powershell
pip install kohakuterrarium
# 如果不加虚拟环境又报错，试试用户安装：
# pip install --user kohakuterrarium
```

## kt-biome

这一步别跳。默认 `swe` 依赖它。
```powershell
kt install https://github.com/Kohaku-Lab/kt-biome.git
```

装完能用：
| creature | 用途 |
|----------|------|
| `@kt-biome/creatures/general` | 通用助手 |
| `@kt-biome/creatures/swe` | 软件工程 |
| `@kt-biome/creatures/reviewer` | 代码审查 |
| `@kt-biome/terrariums/swe_team` | 多智能体 |

## 登录模型

Codex OAuth：
```powershell
kt login codex
kt model default gpt-5.4
```

浏览器弹出，授权完显示 `Login successful`。

其他 OpenAI 兼容供应商：
```powershell
kt login openai --api-key YOUR_KEY --base-url https://api.example.com/v1
kt model default gpt-5.4
```

## 跑默认 swe

```powershell
kt run @kt-biome/creatures/swe --mode cli
```

看到：
```
Loading creature: @kt-biome/creatures/swe
Connecting to model: gpt-5.4
Ready. Type your message (Ctrl+C to exit):
```

全屏界面：
```powershell
kt run @kt-biome/creatures/swe --mode tui
```

## 本地扩展示例

有 `examples/agent-apps/swe_bio_agent` 时：
```powershell
kt run examples/agent-apps/swe_bio_agent --mode cli
```

比默认 swe 多两样：硬约束（先读规则文件才能改代码）、审计留痕（操作记 JSONL）。

## 验证

```powershell
kt --version
kt list
kt info @kt-biome/creatures/swe
dir ~/.kohakuterrarium/sessions/*.kohakutr
```

都有就装好了。

有本地扩展时额外验证：
```powershell
kt info examples/agent-apps/swe_bio_agent
dir examples/agent-apps/swe_bio_agent/artifacts/audit/*.jsonl
```

## 常见问题

**`kt` 命令找不到：**PATH 没配好。Windows 加：
```powershell
$env:PATH += ";$(python -m site --user-base)\Scripts"
```

**kt install 超时：**网络问题。确认 git 装了，用代理，或手动 clone。

**Login 失败：**检查 API key、base URL、模型名。

**找不到 session：**默认在 `~/.kohakuterrarium/sessions/`，用 `kt resume --list` 查。
