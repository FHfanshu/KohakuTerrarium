# 前端架构

这篇给维护 Vue 3 Web 仪表盘的人看，主要讲组件树、store 设计、WebSocket 协议，以及怎么加新 panel。

## 开发循环

源码在 `src/kohakuterrarium-frontend/`。构建产物会写到 `src/kohakuterrarium/web_dist/`（见 `vite.config.js:48`），`api/app.py` 和 `serving/web.py` 会把它当成静态文件目录。

```bash
# 开发服务器（热更新，通过代理连到 Python API）
npm run dev --prefix src/kohakuterrarium-frontend

# 生产构建（写入 src/kohakuterrarium/web_dist）
npm run build --prefix src/kohakuterrarium-frontend

# Lint / format
npm run lint   --prefix src/kohakuterrarium-frontend
npm run format --prefix src/kohakuterrarium-frontend

# 单元测试（vitest + jsdom）
npm run test   --prefix src/kohakuterrarium-frontend
```

发布 KT 时，要先跑 `npm run build`，确保 `web_dist/` 已经生成，再执行 `pip install -e .` 或打包。Python 侧发布出去的是已经构建好的前端 bundle。

## 技术栈

- **Vue 3.5+**，使用 `<script setup>` composition API
- **Pinia 3** 做状态管理（chat 用 options API store，layout/canvas/palette 用 composition API）
- **Vite**（rolldown-vite），配合 UnoCSS、unplugin-auto-import、unplugin-vue-components、unplugin-vue-router
- **Element Plus 2.11**，用于对话框、下拉框、选择器、tooltip
- **Monaco Editor**，用于代码编辑
- **Vditor**，用于富文本 Markdown 编辑
- **xterm.js**，用于终端面板
- **highlight.js**，用于 canvas 代码查看器
- **splitpanes**（旧组件，仅老的 `SplitPane.vue` 还在用）

## 目录结构

```
src/kohakuterrarium-frontend/src/
├── App.vue                    # 根组件：NavRail + router-view + 全局 composable
├── main.js                    # Pinia + router + panel 注册（同步执行）
├── style.css                  # 主题变量、字体栈
├── components/
│   ├── chat/                  # ChatPanel, ChatMessage, ToolCallBlock
│   ├── chrome/                # AppHeader, StatusBar, ModelSwitcher,
│   │                            CommandPalette, ToastCenter
│   ├── common/                # StatusDot, SplitPane, GemBadge, MarkdownRenderer
│   ├── editor/                # EditorMain, MonacoEditor, VditorEditor,
│   │                            FileTree, FileTreeNode, EditorStatus
│   ├── layout/                # WorkspaceShell, LayoutNode, EditModeBanner,
│   │                            PanelHeader, PanelPicker, SavePresetModal,
│   │                            NavRail, NavItem, Zone*.vue（旧）
│   ├── panels/                # ActivityPanel, StatePanel, FilesPanel,
│   │                            CreaturesPanel, CanvasPanel, SettingsPanel,
│   │                            DebugPanel, TerminalPanel
│   │   ├── canvas/            # CodeViewer, MarkdownViewer, HtmlViewer
│   │   ├── debug/             # LogsTab, TraceTab, PromptTab, EventsTab
│   │   └── settings/          # ModelTab, PluginsTab, ExtensionsTab 等
│   ├── registry/              # ConfigCard
│   └── status/                # StatusDashboard（大型 tab 状态面板）
├── composables/
│   ├── useKeyboardShortcuts.js  # Ctrl+1..6, Ctrl+Shift+L, Ctrl+K
│   ├── useBuiltinCommands.js    # 命令面板注册
│   ├── useAutoTriggers.js       # Canvas 通知、error→debug
│   ├── useArtifactDetector.js   # 扫描聊天里的代码块并写入 canvas store
│   ├── useLogStream.js          # /ws/logs WebSocket composable
│   └── useFileWatcher.js        # /ws/files WebSocket composable（Windows 上未使用）
├── stores/
│   ├── chat.js                # WebSocket chat、messages、runningJobs、tokenUsage
│   ├── layout.js              # Preset、panel、edit mode、split tree 变更
│   ├── layoutPanels.js        # Panel + preset 注册（由 main.js 调用）
│   ├── canvas.js              # Artifact 检测与存储
│   ├── files.js               # 从聊天事件派生 touched files
│   ├── scratchpad.js          # Scratchpad REST client
│   ├── palette.js             # 命令面板注册 + 模糊搜索
│   ├── notifications.js       # Toast + 历史记录
│   ├── instances.js           # 运行中的实例列表
│   ├── editor.js              # 打开的文件、当前文件、文件树
│   ├── theme.js               # 深色/浅色切换
│   └── ...
├── pages/
│   ├── instances/[id].vue     # 主实例页面（WorkspaceShell）
│   ├── editor/[id].vue        # 编辑器主视图（WorkspaceShell）
│   ├── detached/[key].vue     # 弹出单 panel 页面
│   ├── panel-debug.vue        # 调试页：每个 panel 一个 tab
│   ├── index.vue, new.vue, sessions.vue, registry.vue, settings.vue
│   └── ...
└── utils/
    ├── api.js                 # Axios HTTP client（所有 REST endpoint）
    └── layoutEvents.js        # 跨组件动作的 CustomEvent 总线
```

## 布局系统

### 二叉分割树

布局是一个递归二叉树，每个节点只有两种形态：

```js
// Split：两个子节点，中间有可拖动分隔条
{ type: "split", direction: "horizontal"|"vertical", ratio: 0-100, children: [Node, Node] }

// Leaf：渲染一个 panel
{ type: "leaf", panelId: "chat" }
```

`LayoutNode.vue` 是递归渲染器。遇到 split，就在 flex 容器里渲染两个子节点和一个带 pointer capture 的拖拽手柄；遇到 leaf，就从 layout store 取出对应 panel 组件，用 `<component :is>` 渲染。

### Panel 注册

Panel 在 `stores/layoutPanels.js` 里注册，发生在应用启动时（同步执行，在 `app.mount()` 之前）：

```js
layout.registerPanel({
  id: "chat",
  label: "Chat",
  component: ChatPanel,
});
```

`component` 会在内部用 `markRaw()` 包起来，避免被 Vue 响应式系统代理。

### Preset

Preset 就是一棵布局树，外加 id、label 和可选快捷键：

```js
const CHAT_FOCUS = {
  id: "chat-focus",
  label: "Chat Focus",
  shortcut: "Ctrl+1",
  tree: hsplit(70, leaf("chat"), vsplit(65, leaf("status-dashboard"), leaf("state"))),
};
```

辅助函数 `hsplit(ratio, left, right)`、`vsplit(ratio, top, bottom)` 和 `leaf(panelId)` 用来更简洁地拼树。

### Panel props

路由页面（例如 `pages/instances/[id].vue`）会通过 Vue 的 `provide("panelProps", computed(() => ({...})))` 给 panel 提供运行时参数。`LayoutNode` 会读取它，再按 `panelId` 把对应那一段 props 传给每个 leaf 组件。

### Edit mode

`layout.enterEditMode()` 会深拷贝当前 preset。所有树结构修改（replace、split、close）都只动这份副本。`layout.exitEditMode()` 会恢复原始 preset；`layout.saveEditMode()` 会把副本持久化保存下来（只保存用户 preset）。

## WebSocket 协议

### Chat（`/ws/creatures/{agent_id}` 或 `/ws/terrariums/{id}`）

这部分已经有了，由 `stores/chat.js` 负责。它会流式处理文本片段、tool start/done、token usage、session info 和 compaction 事件。

### Logs（`/ws/logs`）

服务端进程日志 tail。消息格式：`{type: "meta"|"line"|"error", ...}`。
日志行会被解析成 `{ts, level, module, text}`。

### Terminal（`/ws/terminal/{agent_id}`）

运行在 agent 工作目录下的 PTY shell。消息格式：
- Client → Server：`{type: "input", data: "..."}`、`{type: "resize", rows, cols}`
- Server → Client：`{type: "output", data: "..."}`、`{type: "error", data: "..."}`

### Files（`/ws/files/{agent_id}`）

文件系统 watcher（watchfiles）。消息格式：
`{type: "ready"|"change"|"error", ...}`。变更里会带 path 和 action（added/modified/deleted）。目前在 Windows 上不太稳定。

## 新增一个 panel

1. 新建 `components/panels/MyPanel.vue`
2. 在 `stores/layoutPanels.js` 里注册：
   ```js
   import MyPanel from "@/components/panels/MyPanel.vue";
   layout.registerPanel({ id: "my-panel", label: "My Panel", component: MyPanel });
   ```
3. 把它加进某个 preset：
   ```js
   tree: hsplit(50, leaf("chat"), leaf("my-panel"))
   ```
4. 如果这个 panel 需要运行时参数（比如 `instance`），就在路由页面的 `panelProps` computed 里加对应项。

## 主题

`stores/theme.js` 管理深色/浅色模式。组件里通过响应式的 `useThemeStore().dark` 读取状态。CSS 用 `html.dark` 类覆盖深色模式样式，UnoCSS 的 `dark:` 前缀也都是按这个工作。

Vditor 和 xterm.js 各自有自己的主题系统，这两处都会监听 `themeStore.dark`，然后调用各自的主题切换 API。
