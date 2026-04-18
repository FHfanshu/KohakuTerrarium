# Serving

这篇给准备跑 KohakuTerrarium Web UI、桌面应用，或者常驻后台服务的人看。

相关命令有三个：`kt web`（前台 Web 服务器）、`kt app`（用 pywebview 打开的桌面窗口）、`kt serve`（脱离终端运行的守护进程）。三者共用同一套 FastAPI 后端和 Vue 前端，区别主要在运行方式和连接方式。

先补个概念：[agent as a Python object](../concepts/python-native/agent-as-python-object.md)。服务层说白了只是核心运行时的另一种使用方式。

## 我该用哪个？

| 方式 | 生命周期 | 适合什么时候用 |
|---|---|---|
| `kt web` | 前台运行；按 Ctrl+C 退出 | 你想在这台机器的浏览器里打开 `http://127.0.0.1:8001`。 |
| `kt app` | 前台运行；关掉窗口就退出 | 想要更像原生桌面应用的体验。需要 `pywebview`。 |
| `kt serve` | 后台守护进程；终端关了也继续跑 | 长时间运行的 agent、SSH 会话、远程机器、要一直挂着的工作流。 |

三种方式用的 API 和前端都一样，按你想怎么跑来选就行。

## `kt web`

```bash
kt web
kt web --host 0.0.0.0 --port 9000
kt web --dev
kt web --log-level DEBUG
```

- 默认 host 是 `127.0.0.1`，默认端口是 `8001`。端口占用时会自动往后加。
- `--dev` 只启动 API；前端 HMR 需要你另外跑 `npm run dev --prefix src/kohakuterrarium-frontend`。
- 会一直跑到你按 Ctrl+C。

如果前端还没 build，页面里会看到一个占位提示。源码安装时先手动构建一次：

```bash
npm install --prefix src/kohakuterrarium-frontend
npm run build --prefix src/kohakuterrarium-frontend
```

如果你是从 PyPI 安装，构建好的静态资源已经带上了。

## `kt app`

```bash
kt app
kt app --port 8002
```

它会用 pywebview 打开一个桌面窗口，窗口后面连的是内嵌 API 服务器。需要安装桌面相关依赖：

```bash
pip install 'kohakuterrarium[full]'
```

窗口一关，服务器也会停。

## `kt serve`

```bash
kt serve start                  # 后台守护进程
kt serve start --host 0.0.0.0 --port 8001 --dev --log-level INFO
kt serve status                 # running/stopped/stale、PID、URL、运行时长
kt serve logs --follow          # 持续看日志
kt serve logs --lines 200
kt serve stop                   # 先发 SIGTERM，宽限期后默认 5 秒再 SIGKILL
kt serve stop --timeout 30
kt serve restart                # 先停再起
```

状态文件在这里：

```
~/.kohakuterrarium/run/web.pid    # 进程 id
~/.kohakuterrarium/run/web.json   # url、host、port、started_at、git commit、version
~/.kohakuterrarium/run/web.log    # stdout + stderr
```

如果 PID 文件还在，但进程已经没了，`kt serve status` 会显示 `stale`。这时可以删掉 `~/.kohakuterrarium/run/web.*`，也可以直接重新跑 `kt serve start`，它会自己清理。

### 开发模式下的守护进程

```bash
kt serve start --dev
npm run dev --prefix src/kohakuterrarium-frontend
```

这样前端 HMR 走的是守护进程的 API，后台服务也不会跟着终端一起死。

## 什么时候更适合用守护进程

- SSH 会话老断，适合先用 `kt serve start` 跑起来，再用 `ssh -L 8001:localhost:8001` 重连。
- 机器是远程的，你不想一直留个终端窗口挂着。
- 有长期运行的监控 agent，不能因为终端断开就被带死。
- 多个人要连同一个实例。这个场景下可以绑 `--host 0.0.0.0`，但最好前面再挂一个带认证的反向代理，因为 API 自己没有内建认证。

## API 本身

这三种方式暴露出来的都是同一个 FastAPI 应用：

- REST endpoint：`/api/agents`、`/api/terrariums`、`/api/creatures`、`/api/channels`、`/api/configs`、`/api/sessions`
- WebSocket endpoint：流式聊天、channel 观察、日志 tail

完整列表见[参考 / HTTP API](../reference/http.md)。

## 排错

- **`kt web` 打印出 "frontend not built"。** 按上面的步骤先 build，或者改用 `kt web --dev`，再单独跑 `vite dev`。
- **`kt serve status` 显示 `stale`。** 多半是之前被 `kill -9` 之后留下了旧 PID 文件。重新跑一次 `kt serve start` 就会清掉，或者手动删 `~/.kohakuterrarium/run/web.*`。
- **两个实例都在抢 8001 端口。** `kt web` 会自动换下一个端口；`kt serve` 如果端口被占，会直接报错。自己用 `--port` 指定。
- **`kt web` 没自动打开浏览器。** 它只会把 URL 打出来，要自己打开。
- **别的机器连不上守护进程。** 你大概率绑的是 `127.0.0.1`。重启时改成 `--host 0.0.0.0`，前面再加代理。
- **`kt app` 一启动就崩。** 一般是没装 `pywebview`。装 `pip install 'kohakuterrarium[full]'`，或者先退回 `kt web`。

## 另见

- 前端布局 —— UI 里有哪些面板和预设。
- [参考 / HTTP API](../reference/http.md) —— REST 和 WebSocket endpoint。
- [参考 / CLI](../reference/cli.md) —— `kt web`、`kt app`、`kt serve` 的参数说明。
- [ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md) —— 之后计划做的守护进程工作流。
