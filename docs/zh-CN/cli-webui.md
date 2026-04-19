# CLI 与 WebUI 使用

KohakuTerrarium 常见的交互方式有三种：命令行、Web 界面和桌面应用。这篇主要讲怎么上手使用它们。

## 命令速查

| 命令 | 做什么 |
|------|--------|
| `kt run` | 跑一个智能体 |
| `kt terrarium run` | 跑多智能体拓扑 |
| `kt serve` | 启动后端服务 |
| `kt web` | 打开 Web 界面 |
| `kt app` | 打开桌面应用 |

## 命令行操作

### 模型相关

```powershell
# 登录
kt login codex

# 看有哪些模型
kt model list

# 设置默认模型
kt model default gpt-5.4

# 查看当前模型详情
kt model show gpt-5.4
```

### 跑智能体

```powershell
# 基本用法
kt run @kt-biome/creatures/swe --mode cli

# 跑本地扩展示例（需要在项目根目录下，且该目录确实存在）
kt run examples/agent-apps/swe_bio_agent --mode cli

# 全屏界面
kt run examples/agent-apps/swe_bio_agent --mode tui
```

> `examples/agent-apps/swe_bio_agent` 不是官方远端仓库当前默认自带内容。
> 没有这个目录时，请改用 `@kt-biome/creatures/swe`。

常用参数：

| 参数 | 作用 |
|------|------|
| `--mode cli` | 普通命令行交互（默认） |
| `--mode tui` | 全屏终端界面 |
| `--mode plain` | 纯输入输出，适合脚本调用 |
| `--llm <profile>` | 临时换个模型 |
| `--session <path>` | 指定 session 存放位置 |
| `--no-session` | 不保存 session |
| `--log-level DEBUG` | 打最详细的日志 |

### 查看智能体信息

```powershell
kt info @kt-biome/creatures/swe
```

输出大概这样：

```
Name: swe
...
```

### 恢复上次的会话

```powershell
# 交互式选择
kt resume

# 接着最近那次
kt resume --last

# 按名字找
kt resume swe_bio_agent
```

### 搜历史会话

```powershell
# 关键词搜
kt search "read AGENTS.md"

# 精确搜索
kt search "blocked bash command" --mode fts

# 语义搜索（需要 embedding 模型）
kt search "read rule file" --mode semantic
```

## WebUI

### 启动流程

```powershell
# 1. 启动后端
kt serve start 

# 2. 看看有没有跑起来
kt serve status

# 3. 看日志
kt serve logs

# 或者直接打开web界面（不用kt serve，适合本地开发场景（？）
kt web
```

看到 `Server running at http://localhost:8001` 就说明后端起来了。

> 从源码跑的话，得先构建前端：
> ```powershell
> npm install --prefix src/kohakuterrarium-frontend
> npm run build --prefix src/kohakuterrarium-frontend
> ```

### WebUI 能做什么

| 功能 | 说明 |
|------|------|
| 会话管理 | 创建、恢复、搜索历史会话 |
| 智能体选择 | 从已装的包里选，或加载本地配置 |
| 实时对话 | 流式输出、工具调用可视化 |
| 日志查看 | 看服务端日志和事件流 |

### 服务管理

```powershell
kt serve stop       # 停
kt serve restart    # 重启
kt serve status -v   # 详细状态
```

## 桌面应用

```powershell
kt app
```

本质上就是把 WebUI 包成了桌面窗口，不用手动启动服务，也会带系统托盘图标。

## 选哪个？

| 你的场景 | 用这个 |
|----------|--------|
| 快速试一下功能 | `kt run ... --mode cli` |
| 想完整交互面板 | `--mode tui` |
| 长期运行、多人协作 | `kt serve` |
| 想桌面应用体验 | `kt app` |
| 脚本自动化 | `--mode plain` |

## 新手推荐路径

1. `kt run @kt-biome/creatures/swe --mode cli` — 先熟悉默认行为
2. 如果你本地有扩展示例，再跑 `kt run examples/agent-apps/swe_bio_agent --mode cli` — 体验带强约束的版本
3. `kt serve start` + `kt web` — 试试 WebUI

## 常见问题

### 端口被占了

```powershell
kt serve start --port 8080
```

### WebUI 打开但连不上

1. `kt serve status` — 确认服务在跑
2. 检查防火墙
3. 确认访问的是 `http://localhost:8001`

### TUI 界面显示乱码

尽量用 Windows Terminal 或 iTerm2 这类现代终端；如果还是不理想，就直接改用 `--mode cli`。

---

[配置文件写法 →](configuration)
