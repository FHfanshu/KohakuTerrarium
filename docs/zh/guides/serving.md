# 服务方式

给要运行 KohakuTerrarium Web UI、桌面应用，或长期驻留守护进程的读者。

这里有三个命令：`kt web`（前台 Web 服务器）、`kt app`（通过 pywebview 打开的桌面窗口）、`kt serve`（脱离终端运行的守护进程）。三者共用同一套 FastAPI 后端和 Vue 前端，差别主要在生命周期和传输方式。

概念预备：[agent as a Python object](/concepts/python-native/agent-as-python-object.md)（英文）—— serving 层只是核心运行时的另一种使用方式。

## 我该用哪个？

| 方式 | 生命周期 | 适合什么场景 |
|---|---|---|
| `kt web` | 前台运行；按 Ctrl+C 退出 | 你想在这台机器的浏览器里打开 `http://127.0.0.1:8001`。 |
| `kt app` | 前台运行；关掉窗口就退出 | 想要更像原生应用的桌面体验。需要 `pywebview`。 |
| `kt serve` | 守护进程；终端关掉后还继续运行 | 长时间运行的 agent、SSH 会话、远程机器、需要持续存在的工作流。 |

三者使用同一套 API 和前端。按生命周期来选就行。

## `kt web`

```bash
kt web
kt web --host 0.0.0.0 --port 9000
kt web --dev
kt web --log-level DEBUG
```

- 默认 host 是 `127.0.0.1`，端口是 `8001`（如果被占用，会自动递增）。
- `--dev` 只提供 API；前端热更新要单独运行 `npm run dev --prefix src/kohakuterrarium-frontend`。
- 会一直运行，直到你按 Ctrl+C。

如果前端还没构建，你会看到一个占位页。源码安装时先构建一次：

```bash
npm install --prefix src/kohakuterrarium-frontend
npm run build --prefix src/kohakuterrarium-frontend
```

如果是通过 PyPI 安装，构建好的静态资源已经打包好了。

## `kt app`

```bash
kt app
kt app --port 8002
```

它会用 pywebview 打开一个原生桌面窗口，连接到内嵌的 API 服务器。需要安装桌面相关依赖：

```bash
pip install 'kohakuterrarium[full]'
```

窗口一关，服务器也会停止。

## `kt serve`

```bash
kt serve start                  # 脱离终端运行的守护进程
kt serve start --host 0.0.0.0 --port 8001 --dev --log-level INFO
kt serve status                 # running/stopped/stale、PID、URL、运行时长
kt serve logs --follow          # 持续跟踪守护进程日志
kt serve logs --lines 200
kt serve stop                   # 先发 SIGTERM 并等待宽限期（默认 5 秒），再发 SIGKILL
kt serve stop --timeout 30
kt serve restart                # 先停再启
```

状态文件：

```
~/.kohakuterrarium/run/web.pid    # 进程 id
~/.kohakuterrarium/run/web.json   # url、host、port、started_at、git commit、version
~/.kohakuterrarium/run/web.log    # stdout + stderr
```

如果 PID 文件还在，但进程已经没了，`kt serve status` 会显示 `stale`。可以手动删除 `rm ~/.kohakuterrarium/run/web.*`，也可以直接运行 `kt serve start`，它会顺手清理。

### 开发模式下的守护进程

```bash
kt serve start --dev
npm run dev --prefix src/kohakuterrarium-frontend
```

这样前端的 HMR 会连到守护进程 API，同时守护进程本身不受当前终端影响。

## 什么时候更适合用守护进程

- SSH 会话总断：用 `kt serve start` 跑起来，然后通过 `ssh -L 8001:localhost:8001` 重新连回来。
- 远程机器上不想一直挂着一个终端窗口。
- 监控类 agent 需要长期运行，不能因为终端丢了就被杀掉。
- 多个用户要连到同一个实例（可以绑定 `--host 0.0.0.0`，但最好前面加带认证的反向代理，因为 API 本身没有内置认证）。

## API 本身

这三种方式暴露的都是同一个 FastAPI 应用：

- REST 端点在 `/api/agents`、`/api/terrariums`、`/api/creatures`、`/api/channels`、`/api/configs`、`/api/sessions`
- WebSocket 端点用于流式聊天、channel 观察和日志 tail

完整端点列表见：[Reference / HTTP API](/reference/http.md)（英文）。

## 排错

- **`kt web` 打印 `frontend not built`。** 按上面的步骤构建前端，或者用 `kt web --dev`，然后单独运行 `vite dev`。
- **`kt serve status` 显示 `stale`。** 一般是被 `kill -9` 后留下的旧 PID 文件。重新跑一次 `kt serve start` 就会清掉，或者手动删掉 `~/.kohakuterrarium/run/web.*`。
- **两个实例都在抢 8001 端口。** `kt web` 会自动递增端口；`kt serve` 如果配置的端口已被占用，会直接失败。用 `--port` 指定别的端口。
- **`kt web` 没有自动打开浏览器。** 它只会打印 URL，需要你自己打开。
- **从别的主机访问不到守护进程。** 你绑定的是 `127.0.0.1`。用 `--host 0.0.0.0` 重启，并放到代理后面。
- **`kt app` 一启动就崩。** 多半是没装 `pywebview`。运行 `pip install 'kohakuterrarium[full]'`，或者改用 `kt web`。

## 另见

- [Frontend Layout](/guides/frontend-layout.md)（英文）—— UI 里有哪些面板和预设。
- [Reference / HTTP API](/reference/http.md)（英文）—— REST 和 WebSocket 端点。
- [Reference / CLI](/reference/cli.md)（英文）—— `kt web`、`kt app`、`kt serve` 的参数。
- [ROADMAP](https://github.com/Kohaku-Lab/KohakuTerrarium/blob/main/ROADMAP.md)（英文）—— 计划中的守护进程工作流。
