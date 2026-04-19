# HTTP 与 WebSocket API

这里是包里 FastAPI 服务器对外开的所有 REST endpoint 和 WebSocket 通道（`kt web`、`kt serve`、`python -m kohakuterrarium.api.main`）。
API 一方面给 Vue SPA 用，另一方面也适合那些想从进程外控制 agent 和 terrarium 的客户端。

服务层和 session 存储的结构，见[会话持久化](/concepts/impl-notes/session-persistence.md)。
如果你更关心面向任务的用法，见[程序化使用](/zh/programmatic-usage.md)和[前端布局](/zh/frontend-layout.md)。

## 服务器配置

- 默认 host：`0.0.0.0`。
- 默认端口：`8001`（如果用 `kt web`，端口被占了就继续往上试）。
- 可通过 `python -m kohakuterrarium.api.main --host 127.0.0.1 --port 8080 [--reload]` 覆盖。
- `KT_SESSION_DIR` 会覆盖默认的 session 目录。
- CORS 完全开放：`allow_origins=["*"]`，允许所有方法和所有 headers。
- 没有认证。把这个服务器当成本机可信服务来用。
- 版本字符串：`0.1.0`。URL 没有 `/v1/` 前缀。
- FastAPI 自动文档：`/docs`（Swagger UI）、`/redoc`（ReDoc）。

当 `create_app(static_dir=Path)` 传入一个有效的已构建 SPA 目录时：

- `/assets/*` — 带哈希的构建资源。
- `/{path}` — SPA 回退路由，任何未匹配路径都返回 `index.html`。
- `/api/*` 和 WebSocket 路由优先匹配。

## 响应约定

- 状态码：`200` 表示成功，`400` 是输入有问题，`404` 是资源不存在，`500` 是服务器错误。不用 `201`。
- 除非另有说明，payload 都是 JSON。
- 错误使用 FastAPI 的 `HTTPException`，格式为 `{"detail": "<message>"}`。

---

## Terrariums

### `POST /api/terrariums`

根据配置路径创建并启动一个 terrarium。

- 请求体：`TerrariumCreate`（`config_path`、可选 `llm`、`pwd`）。
- 响应：`{"terrarium_id": str, "status": "running"}`。
- 状态码：`200`、`400`。
- 副作用：生成 terrarium；初始化 root agent；启动 creatures；如果配置了 session store，也会一并打开。

### `GET /api/terrariums`

列出所有正在运行的 terrarium，返回状态对象数组（结构与下面的单个 terrarium GET 相同）。

### `GET /api/terrariums/{terrarium_id}`

返回一个 `TerrariumStatus`：`terrarium_id`、`name`、`running`、`creatures`（name → status dict）、`channels`（channel 名称列表）。

### `DELETE /api/terrariums/{terrarium_id}`

停止并清理一个 terrarium。响应：`{"status": "stopped"}`。副作用：停止所有 creatures，清理 channels，关闭 session store。

### `POST /api/terrariums/{terrarium_id}/channels`

在运行时添加一个 channel。

- 请求体：`ChannelAdd`（`name`、默认值为 `"queue"` 的 `channel_type`、`description`）。
- 响应：`{"status": "created", "channel": <name>}`。

### `GET /api/terrariums/{terrarium_id}/channels`

列出 channels，格式为 `[{"name", "type", "description"}]`。

### `POST /api/terrariums/{terrarium_id}/channels/{channel_name}/send`

向某个 channel 注入一条消息。

- 请求体：`ChannelSend`（`content`，类型为 `str` 或 `list[ContentPartPayload]`；`sender` 默认 `"human"`）。
- 响应：`{"message_id": str, "status": "sent"}`。
- 副作用：消息会写入历史记录；监听器会触发各自的 `on_send` 回调。

### `POST /api/terrariums/{terrarium_id}/chat/{target}`

非流式聊天。`target` 可以写成 `"root"`，也可以写某个 creature 名。

- 请求体：`AgentChat`（`message` 或 `content`）。
- 响应：`{"response": <full text>}`。

### `GET /api/terrariums/{terrarium_id}/history/{target}`

读对话和事件日志。`target` 可以是 `"root"`、某个 creature 名，或者 channel 历史用的 `"ch:<channel_name>"`。会先读 SessionStore，读不到再回退到内存日志。

- 响应：`{"terrarium_id", "target", "messages": [...], "events": [...]}`。

### `GET /api/terrariums/{terrarium_id}/scratchpad/{target}`

返回目标 agent 的 scratchpad，格式为 `{key: value}`。

### `PATCH /api/terrariums/{terrarium_id}/scratchpad/{target}`

- 请求体：`ScratchpadPatch`（`updates: {key: value | null}`；`null` 表示删除）。
- 响应：更新后的 scratchpad。

### `GET /api/terrariums/{terrarium_id}/triggers/{target}`

列出当前启用的远程 trigger：
`[{"trigger_id", "trigger_type", "running", "created_at"}]`。

### `GET /api/terrariums/{terrarium_id}/plugins/{target}`

列出已加载的 plugins 以及启用/禁用状态。

### `POST /api/terrariums/{terrarium_id}/plugins/{target}/{plugin_name}/toggle`

切换 plugin 状态。响应：`{"name", "enabled"}`。启用时会调用 `load_pending()`。

### `GET /api/terrariums/{terrarium_id}/env/{target}`

返回 `{"pwd", "env"}`。env 里只要键名带 `secret`、`key`、`token`、`password`、`pass`、`private`、`auth`、`credential`（大小写不敏感），就会被过滤掉。

### `GET /api/terrariums/{terrarium_id}/system-prompt/{target}`

返回 `{"text": <assembled system prompt>}`。

---

## Creatures（terrarium 内）

### `GET /api/terrariums/{terrarium_id}/creatures`

返回 creature 名称到状态 dict 的映射。

### `POST /api/terrariums/{terrarium_id}/creatures`

在运行时添加一个 creature。

- 请求体：`CreatureAdd`（`name`、`config_path`、`listen_channels`、`send_channels`）。
- 响应：`{"creature": <name>, "status": "running"}`。

### `DELETE /api/terrariums/{terrarium_id}/creatures/{name}`

移除一个 creature。响应：`{"status": "removed"}`。

### `POST /api/terrariums/{terrarium_id}/creatures/{name}/interrupt`

中断该 creature 当前的 `agent.process()`，但不终止它。响应：`{"status": "interrupted", "creature": <name>}`。

### `GET /api/terrariums/{terrarium_id}/creatures/{name}/jobs`

返回正在运行和排队中的后台 jobs。

### `POST /api/terrariums/{terrarium_id}/creatures/{name}/tasks/{job_id}/stop`

取消一个正在运行的后台 job。响应：`{"status": "cancelled", "job_id"}`。

### `POST /api/terrariums/{terrarium_id}/creatures/{name}/promote/{job_id}`

把一个直接任务提升到后台队列。

### `POST /api/terrariums/{terrarium_id}/creatures/{name}/model`

不重启，直接切换该 creature 的 LLM。

- 请求体：`ModelSwitch`（`model`）。
- 响应：`{"status": "switched", "creature", "model"}`。

### `POST /api/terrariums/{terrarium_id}/creatures/{name}/wire`

为某个 channel 添加 listen 或 send 绑定。

- 请求体：`WireChannel`（`channel`、`direction` = `"listen"` 或 `"send"`）。
- 响应：`{"status": "wired"}`。

---

## 独立 agents

### `POST /api/agents`

创建并启动一个不属于任何 terrarium 的 agent。

- 请求体：`AgentCreate`（`config_path`、可选 `llm`、`pwd`）。
- 响应：`{"agent_id", "status": "running"}`。

### `GET /api/agents`

列出正在运行的 agents。

### `GET /api/agents/{agent_id}`

返回 `{"agent_id", "name", "model", "running"}`。

### `DELETE /api/agents/{agent_id}`

停止该 agent。响应：`{"status": "stopped"}`。

### `POST /api/agents/{agent_id}/interrupt`

中断当前处理。

### `POST /api/agents/{agent_id}/regenerate`

用当前模型和设置重新生成上一条 assistant 响应。
响应：`{"status": "regenerating"}`。

### `POST /api/agents/{agent_id}/messages/{msg_idx}/edit`

修改一条用户消息，并从该位置重新执行。

- 请求体：`MessageEdit`（`content`）。
- 响应：`{"status": "edited"}`。
- 副作用：会在 `msg_idx` 处截断历史，注入新消息，然后重放。

### `POST /api/agents/{agent_id}/messages/{msg_idx}/rewind`

截断对话，但不重新执行。响应：
`{"status": "rewound"}`。

### `POST /api/agents/{agent_id}/promote/{job_id}`

把一个直接任务提升到后台。

### `GET /api/agents/{agent_id}/plugins`

列出 plugins 及其状态。

### `POST /api/agents/{agent_id}/plugins/{plugin_name}/toggle`

启用或禁用一个 plugin。响应：`{"name", "enabled"}`。

### `GET /api/agents/{agent_id}/jobs`

列出后台 jobs。

### `POST /api/agents/{agent_id}/tasks/{job_id}/stop`

取消一个后台 job。

### `GET /api/agents/{agent_id}/history`

返回 `{"agent_id", "events": [...]}`。

### `POST /api/agents/{agent_id}/model`

切换该 agent 的 LLM。

- 请求体：`ModelSwitch`（`model`）。
- 响应：`{"status": "switched", "model"}`。

### `POST /api/agents/{agent_id}/command`

执行一条用户 slash command（例如 `model`、`status`）。

- 请求体：`SlashCommand`（`command`、可选 `args`）。
- 响应：取决于具体命令。

### `POST /api/agents/{agent_id}/chat`

非流式聊天。

- 请求体：`AgentChat`。
- 响应：`{"response": <full text>}`。

### `GET /api/agents/{agent_id}/scratchpad`

返回 scratchpad 键值映射。

### `PATCH /api/agents/{agent_id}/scratchpad`

- 请求体：`ScratchpadPatch`。
- 响应：更新后的 scratchpad。

### `GET /api/agents/{agent_id}/triggers`

当前活跃的 triggers，格式为 `[{trigger_id, trigger_type, running, created_at}]`。

### `GET /api/agents/{agent_id}/env`

返回 `{"pwd", "env"}`，其中 secrets 会被过滤。

### `GET /api/agents/{agent_id}/system-prompt`

返回 `{"text": <system prompt>}`。

---

## 配置发现

### `GET /api/configs/creatures`

列出可发现的 creature 配置：
`[{"name", "path", "description"}]`。路径可能是绝对路径，也可能是包内引用。

### `GET /api/configs/terrariums`

列出可发现的 terrarium 配置（结构同上）。

### `GET /api/configs/server-info`

返回 `{"cwd", "platform"}`。

### `GET /api/configs/models`

列出所有已配置的 LLM model/profile 及其可用性。

### `GET /api/configs/commands`

列出 slash commands：`[{"name", "aliases", "description", "layer"}]`。

---

## Registry 与包管理

### `GET /api/registry`

扫描本地目录和已安装包。返回
`[{"name", "type", "description", "model", "tools", "path", "source", ...}]`。
`source` 的值是 `"local"` 或某个包名。

### `GET /api/registry/remote`

从内置的 `registry.json` 返回 `{"repos": [...]}`。

### `POST /api/registry/install`

- 请求体：`InstallRequest`（`url`、可选 `name`）。
- 响应：`{"status": "installed", "name"}`。

### `POST /api/registry/uninstall`

- 请求体：`UninstallRequest`（`name`）。
- 响应：`{"status": "uninstalled", "name"}`。

---

## Sessions

### `GET /api/sessions`

列出已保存的 sessions。

查询参数：

| Param | Type | Default | Description |
|---|---|---|---|
| `limit` | int | `20` | 最多返回多少个 sessions。 |
| `offset` | int | `0` | 跳过前 N 个。 |
| `search` | str | — | 按名称、配置、agents、预览文本过滤（不区分大小写）。 |
| `refresh` | bool | `false` | 强制重建 session 索引。 |

响应：

```json
{
  "sessions": [
    {
      "name": "...", "filename": "...", "config_type": "agent|terrarium",
      "config_path": "...", "agents": [...], "terrarium_name": "...",
      "status": "...", "created_at": "...", "last_active": "...",
      "preview": "...", "pwd": "..."
    }
  ],
  "total": 123,
  "offset": 0,
  "limit": 20
}
```

副作用：首次请求或 30 秒后会重建索引。

### `DELETE /api/sessions/{session_name}`

删除一个 session 文件。响应：`{"status": "deleted", "name"}`。支持传 stem 或完整文件名。

### `POST /api/sessions/{session_name}/resume`

恢复一个已保存的 session。

- 响应：`{"instance_id", "type": "agent"|"terrarium", "session_name"}`。
- 状态码：`200`、`400`（前缀有歧义）、`404`、`500`。

### `GET /api/sessions/{session_name}/history`

返回 session 元数据和可用 targets。

- 响应：`{"session_name", "meta", "targets"}`，其中 targets 包含 agent 名称、`"root"` 以及 `"ch:<channel>"` 项。

### `GET /api/sessions/{session_name}/history/{target}`

读取只读的已保存历史。`target` 需要 URL 编码；可接受 `"root"`、creature 名称或 `"ch:<channel_name>"`。

- 响应：`{"session_name", "target", "meta", "messages", "events"}`。

### `GET /api/sessions/{session_name}/memory/search`

在已保存 session 上执行 FTS5 / semantic / hybrid 搜索。

查询参数：

| Param | Type | Default | Description |
|---|---|---|---|
| `q` | str | required | 查询内容。 |
| `mode` | `auto\|fts\|semantic\|hybrid` | `auto` | 搜索模式。 |
| `k` | int | `10` | 最大结果数。 |
| `agent` | str | — | 按 agent 过滤。 |

响应：`{"session_name", "query", "mode", "k", "count", "results"}`。
每条结果的格式：`{content, round, block, agent, block_type, score, ts, tool_name, channel}`。

副作用：未建立索引的 events 会被补建索引（幂等）；如果 agent 正在运行，会使用实时 embedder，否则从配置加载。

---

## 文件

### `GET /api/files/tree`

返回嵌套文件树。

查询参数：`root`（必填）、`depth`（默认 `3`，限制在 `1..10`）。

响应：递归对象
`{"name", "path", "type": "directory"|"file", "children": [...], "size"}`。

### `GET /api/files/browse`

给文件系统 UI 用的目录浏览视图。

查询参数：`path`（可选）。

响应：
`{"current": {...}, "parent": str|null, "roots": [...], "directories": [...]}`。

### `GET /api/files/read`

读取文本文件。

- 查询参数：`path`（必填）。
- 响应：`{"path", "content", "size", "modified", "language"}`。
- 错误：二进制文件、权限不足 → `400`；文件不存在 → `404`。

### `POST /api/files/write`

- 请求体：`FileWrite`（`path`、`content`）。
- 响应：`{"success": true, "size"}`。
- 副作用：会创建父目录。

### `POST /api/files/rename`

- 请求体：`FileRename`（`old_path`、`new_path`）。
- 响应：`{"success": true}`。

### `POST /api/files/delete`

删除文件或空目录。

- 请求体：`FileDelete`（`path`）。
- 响应：`{"success": true}`。

### `POST /api/files/mkdir`

递归创建目录。

- 请求体：`FileMkdir`（`path`）。
- 响应：`{"success": true}`。

---

## 设置与配置

### API keys

#### `GET /api/settings/keys`

返回 `{"providers": [{"provider", "backend_type", "env_var", "has_key", "masked_key", "available", "built_in"}]}`。

#### `POST /api/settings/keys`

- 请求体：`ApiKeyRequest`（`provider`、`key`）。
- 响应：`{"status": "saved", "provider"}`。

#### `DELETE /api/settings/keys/{provider}`

响应：`{"status": "removed", "provider"}`。

### Codex

#### `POST /api/settings/codex-login`

在服务端执行 Codex OAuth 流程（服务器必须运行在本地）。响应：
`{"status": "ok", "expires_at"}`。

#### `GET /api/settings/codex-status`

返回 `{"authenticated", "expired"?}`。

#### `GET /api/settings/codex-usage`

获取过去 14 天的 Codex 使用量。状态码：`200`、`401`（token 刷新失败）、`404`（未登录）。

### Backends

#### `GET /api/settings/backends`

`{"backends": [{"name", "backend_type", "base_url", "api_key_env", "built_in", "has_token", "available"}]}`。

#### `POST /api/settings/backends`

- 请求体：`BackendRequest`（`name`、默认值为 `"openai"` 的 `backend_type`、`base_url`、`api_key_env`）。
- 响应：`{"status": "saved", "name"}`。

#### `DELETE /api/settings/backends/{name}`

响应：`{"status": "deleted", "name"}`。内置 backend 不能删除（`400`）。

### Profiles

#### `GET /api/settings/profiles`

`{"profiles": [...]}`，字段包括 `name, model, provider, backend_type, base_url, api_key_env, max_context, max_output, temperature, reasoning_effort, service_tier, extra_body`。

#### `POST /api/settings/profiles`

- 请求体：`ProfileRequest`。
- 响应：`{"status": "saved", "name"}`。

#### `DELETE /api/settings/profiles/{name}`

响应：`{"status": "deleted", "name"}`。

#### `GET /api/settings/default-model`

`{"default_model"}`。

#### `POST /api/settings/default-model`

- 请求体：`DefaultModelRequest`（`name`）。
- 响应：`{"status": "set", "default_model"}`。

#### `GET /api/settings/models`

与 `GET /api/configs/models` 相同。

### UI 偏好

#### `GET /api/settings/ui-prefs`

`{"values": {...}}`。

#### `POST /api/settings/ui-prefs`

- 请求体：`UIPrefsUpdateRequest`（`values`）。
- 响应：`{"values": <merged>}`。

### MCP

#### `GET /api/settings/mcp`

`{"servers": [{"name", "transport", "command", "args", "env", "url"}]}`。

#### `POST /api/settings/mcp`

- 请求体：`MCPServerRequest`。
- 响应：`{"status": "saved", "name"}`。

#### `DELETE /api/settings/mcp/{name}`

响应：`{"status": "removed", "name"}`。

---

## WebSocket endpoints

所有 WebSocket endpoint 都通过标准 upgrade 双向通信（没有自定义 headers，也没有 subprotocols）。客户端会收到持续的 JSON frames，也可以发送输入 frames。发生错误时服务器会关闭连接；没有自动重连，也没有 heartbeat，这部分由客户端自己处理。

### `WS /ws/terrariums/{terrarium_id}`

整个 terrarium 的统一事件流（root + creatures + channels）。

入站 frames：

- `{"type": "input", "target": "root"|<creature>, "content": str|list[dict], "message"?: str}` — 将输入排队到目标对象。服务器会回一个确认：
  `{"type": "idle", "source": <target>, "ts": float}`。
- 其他消息类型会被忽略。

出站 frames：

- `{"type": "activity", "activity_type": ..., "source", "ts", ...}` — `activity_type` 包括 `session_info`、`tool_call`、`tool_result`、`token_usage`、`job_update`、`job_completed` 等（见[Event types](/reference/http.md#event-types)）。
- `{"type": "text", "content", "source", "ts"}` — 流式文本分片。
- `{"type": "processing_start", "source", "ts"}`。
- `{"type": "processing_end", "source", "ts"}`。
- `{"type": "channel_message", "source": "channel", "channel", "sender", "content", "message_id", "timestamp", "ts", "history"?: bool}` —
  如果 `history` 为 `true`，表示这是连接建立前消息的回放。
- `{"type": "error", "content", "source"?, "ts"}`。
- `{"type": "idle", "source"?, "ts"}`。

生命周期：

- 连接会立刻接受；如果 terrarium 不存在，会在 upgrade 前返回 `404`。
- 会先回放 channel 历史。
- 之后实时推送事件。
- 客户端关闭连接时会正常清理；服务端会解除输出绑定并移除回调。

### `WS /ws/creatures/{agent_id}`

独立 agent 的事件流。

入站 frames：`{"type": "input", "content": str|list[dict], "message"?: str}`。

出站 frames：与 terrarium 流相同的 `activity` / `text` / `processing_*` / `error` /
`idle` 几类。第一条事件一定是
`{"type": "activity", "activity_type": "session_info", "source", "model", "agent_name", "ts"}`。

### `WS /ws/agents/{agent_id}/chat`

更简单的请求-响应式聊天通道。

入站：`{"message": str}`。

出站：`{"type": "text", "content"}`、`{"type": "done"}`、
`{"type": "error", "content"}`。

连接会在多轮对话之间保持打开。
