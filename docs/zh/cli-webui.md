# CLI 与 WebUI 使用

KohakuTerrarium 有三种交互界面：`kt web`（前台 Web 服务器）、`kt app`（桌面窗口，通过 pywebview）、`kt serve`（后台守护进程）。它们共用同一个 FastAPI 后端和 Vue 前端，区别只在于生命周期和传输方式。

概念入门：[智能体作为 Python 对象](../concepts/python-native/agent-as-python-object.md) —— 服务层只是核心运行时的又一个消费者。

## 选哪个？

| 界面 | 生命周期 | 适用场景 |
|------|----------|----------|
| `kt web` | 前台运行；Ctrl+C 退出 | 你想在本机浏览器打开 `http://127.0.0.1:8001` |
| `kt app` | 前台运行；关闭窗口退出 | 想要原生桌面应用体验。需要安装 `pywebview` |
| `kt serve` | 后台守护进程；退出终端也不会停 | 长期运行的智能体、SSH 会话、远程服务器、持久化工作流 |

三种界面用同样的 API 和前端。根据生命周期选择。

## `kt web`

```bash
kt web
kt web --host 0.0.0.0 --port 9000
kt web --dev
kt web --log-level DEBUG
```

- 默认主机 `127.0.0.1`，端口 `8001`（端口被占用会自动递增）
- `--dev` 只启动 API；需要单独运行 `npm run dev --prefix src/kohakuterrarium-frontend` 来获得前端热更新
- 运行到 Ctrl+C 为止

如果没有构建前端，你会看到一个占位页面 —— 从源码安装的话需要先构建一次：

```bash
npm install --prefix src/kohakuterrarium-frontend
npm run build --prefix src/kohakuterrarium-frontend
```

PyPI 安装版本自带构建好的前端资源。

## `kt app`

```bash
kt app
kt app --port 8002
```

用 pywebview 打开一个原生桌面窗口，连接到内嵌的 API 服务器。需要安装桌面扩展：

```bash
pip install 'kohakuterrarium[full]'
```

关闭窗口时服务器会停止。

## `kt serve`

```bash
kt serve start                  # 启动后台守护进程
kt serve start --host 0.0.0.0 --port 8001 --dev --log-level INFO
kt serve status                 # 查看状态：running/stopped/stale，PID，URL，运行时长
kt serve logs --follow          # 实时查看守护进程日志
kt serve logs --lines 200       # 查看最近 200 行日志
kt serve stop                   # SIGTERM + 等待（默认 5 秒）然后 SIGKILL
kt serve stop --timeout 30      # 等待 30 秒
kt serve restart                # 停止后重新启动
```

状态文件位置：

```
~/.kohakuterrarium/run/web.pid    # 进程 ID
~/.kohakuterrarium/run/web.json   # URL、主机、端口、启动时间、git commit、版本
~/.kohakuterrarium/run/web.log    # stdout + stderr
```

如果 PID 文件存在但进程不存在，`kt serve status` 会报告 `stale` —— 删除 `~/.kohakuterrarium/run/web.*` 或让 `kt serve start` 自动清理。

### 开发模式守护进程

```bash
kt serve start --dev
npm run dev --prefix src/kohakuterrarium-frontend
```

前端热更新连接守护进程 API，守护进程不会因为终端关闭而停止，两边都兼顾。

## 什么时候用守护进程

- SSH 会话经常断开 —— 用 `kt serve start` + `ssh -L 8001:localhost:8001` 端口转发
- 远程服务器不想一直开终端
- 长期监控智能体，不应该因为终端丢失而被杀掉
- 多个用户连接同一个实例（绑定 `--host 0.0.0.0`，但要用反向代理加认证 —— API 本身没有内置认证）

## API 本身

三种界面暴露的是同一个 FastAPI 应用：

- REST 端点：`/api/agents`、`/api/terrariums`、`/api/creatures`、`/api/channels`、`/api/configs`、`/api/sessions`
- WebSocket 端点：流式对话、channel 观察、日志跟踪

完整端点列表：[HTTP API 参考](../reference/http.md)。

## 命令行模式（kt run）

除了 Web 界面，你也可以直接在命令行运行智能体：

```bash
kt run @kt-defaults/creatures/swe --mode cli
```

这会启动一个交互式命令行对话。你可以输入请求，智能体会在当前工作目录使用 shell、文件和编辑工具。Ctrl+C 退出时会打印恢复提示。

三种模式：

| 模式 | 说明 |
|------|------|
| `cli` | 富文本内联显示（TTY 默认） |
| `tui` | 全屏 Textual 应用 |
| `plain` | 纯 stdout/stdin，适合管道或 CI |

临时换模型：

```bash
kt run @kt-defaults/creatures/swe --llm claude-opus-4.6
```

## 恢复会话

会话会自动保存到 `~/.kohakuterrarium/sessions/*.kohakutr`（除非你传了 `--no-session`）。恢复之前任意会话：

```bash
kt resume --last                # 最近一次
kt resume                       # 交互式选择
kt resume swe_20240101_1234     # 按名称前缀
```

智能体会从保存的配置重建，重放对话，重新注册可恢复触发器，恢复 scratchpad 和 channel 历史。详见 [会话](sessions.md)。

## 排错

- **`kt web` 提示 "frontend not built"。** 参考上面的构建步骤，或用 `kt web --dev` 并单独运行 vite dev。
- **`kt serve status` 显示 `stale`。** 之前的进程被 kill -9 了。重新运行 `kt serve start`（会自动清理）或删除 `~/.kohakuterrarium/run/web.*`。
- **两个实例抢占端口 8001。** `kt web` 会自动递增端口；`kt serve` 在端口被占用时会失败。用 `--port` 指定其他端口。
- **`kt web` 没自动打开浏览器。** 它只打印 URL。需要手动打开。
- **从其他主机无法访问守护进程。** 你绑定的是 `127.0.0.1`。用 `--host 0.0.0.0` 重启，并在前面加反向代理。
- **`kt app` 立即崩溃。** 缺少 `pywebview`。用 `pip install 'kohakuterrarium[full]'` 安装，或改用 `kt web`。

## 参考

- [前端布局](../guides/frontend-layout.md) —— UI 里有哪些面板和预设
- [HTTP API 参考](../reference/http.md) —— REST + WebSocket 端点
- [CLI 参考](../reference/cli.md) —— `kt web`、`kt app`、`kt serve` 参数