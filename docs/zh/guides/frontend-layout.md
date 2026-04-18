# 前端布局

这篇给用 `kt web` / `kt app` / `kt serve` 打开 Web 仪表盘，或者想自己改布局的人看。

仪表盘的布局是一棵可配置的二叉分割树。每个窗格要么是叶子节点，也就是一个面板；要么是分割节点，也就是两个子节点，中间带一条可拖动的分隔条。切换 preset 时，会整棵树一起替换。编辑模式则是在当前布局上直接改。

另见：[Serving](serving.md)，这里讲怎么打开仪表盘。

## 核心概念

- **Panel**：只负责一件事的视图，比如 Chat、Files、Activity、State、Canvas、Debug、Settings、Terminal。面板在 `stores/layoutPanels.js` 里注册，通过 id 找到。
- **Split tree**：一棵二叉树。每个节点要么是 *leaf*，渲染一个面板；要么是 *split*，把空间分成两个子节点，中间有可拖动的分隔条。分割可以是 horizontal（左 | 右），也可以是 vertical（上 / 下）。
- **Preset**：一套有名字的分割树配置。切过去时，整棵树会立刻替换掉。preset 可以是内置的，也可以是用户自己建的。
- **Header**：顶部栏，里面有实例信息、preset 下拉菜单、编辑布局按钮、Ctrl+K 命令面板入口，还有停止按钮。
- **Status bar**：底部栏，显示模型切换器、session id、任务数量和运行时间。

## 默认 preset

| 快捷键 | Preset | 布局 |
|--------|--------|------|
| Ctrl+1 | Chat Focus | chat \| status-dashboard（上）+ state（下） |
| Ctrl+2 | Workspace | files \| editor+terminal \| chat+activity |
| Ctrl+3 | Multi-creature | creatures \| chat \| activity+state |
| Ctrl+4 | Canvas | chat \| canvas+activity |
| Ctrl+5 | Debug | chat+state（上）/ debug（下） |
| Ctrl+6 | Settings | settings（全屏） |

实例页面会给 creature 默认选 Chat Focus，给 terrarium 默认选 Multi-creature。每个实例上次用的 preset 会记到 localStorage 里。

## 编辑模式

按 **Ctrl+Shift+L**，或者点 header 里的编辑按钮，就会进入编辑模式。每个面板叶子节点都会显示一条琥珀色工具栏，里面有这些操作：

- **Replace**：打开选择器弹窗，把当前面板换成任意已注册面板
- **Split H / Split V**：把当前叶子节点一分为二，建出一个新的空槽位
- **Close**：移除当前面板，由它的兄弟节点接管父节点空间
- 空槽位上的 **"+ Add panel"** 按钮

顶部的编辑模式横幅提供这些操作：
- **Save**：保存修改（只对用户 preset 生效；内置 preset 不能覆盖）
- **Save as new**：用自定义名称新建一个用户 preset
- **Revert**：丢掉全部修改，恢复原来的布局
- **Exit**：退出编辑模式（如果有未保存修改，会先提示）

所有编辑都发生在 preset 的深拷贝上。只有你明确保存，原始 preset 才会被改掉。

## 键盘快捷键

| 快捷键 | 操作 |
|--------|------|
| Ctrl+1..6 | 切换到 preset |
| Ctrl+Shift+L | 切换编辑模式 |
| Ctrl+K | 打开命令面板 |
| Esc | 退出编辑模式 |

Ctrl+K 就算在输入框有焦点时也会触发。preset 快捷键在文本输入框和 textarea 里会被拦住。

## 命令面板

按 Ctrl+K 打开。它会对所有已注册命令做模糊匹配：

- `Mode: <preset>`：切换到任意 preset
- `Panel: <panel>`：把面板加到它偏好的区域
- `Layout: edit / save as / reset`
- `Debug: open logs`

前缀路由是这样：`>` 是命令（默认），`@` 是 mention，`#` 是 session，`/` 是 slash command。

## 面板

### Chat
主对话界面。支持编辑后重跑消息、重新生成、工具调用折叠面板，还有子 agent 嵌套。

### Activity（标签页）
三个标签：Session（id、cwd、creatures/channels）、Tokens（输入/输出/cache，以及带 compact 阈值的上下文条）、Jobs（正在运行的工具调用，带停止按钮）。

### State（标签页）
四个标签：Scratchpad（agent 工作记忆里的键值对）、Tool History（这个 session 的全部工具调用）、Memory（对 session 事件做 FTS5 搜索）、Compaction（上下文压缩历史）。

### Files
文件树，带刷新功能；还有一个 “Touched” 视图，会按操作分组显示 agent 读过、写过或者报错过的文件。

### Editor
Monaco 编辑器，带文件标签页、未保存标记和 Ctrl+S 保存。对 markdown 文件（`.md` / `.markdown` / `.mdx`），可以在 Monaco（代码模式）和 Vditor（所见即所得的 markdown，带工具栏、数学公式和代码块）之间切换。

### Canvas
会自动识别 assistant 消息里的长代码块（15 行以上）和 `##canvas##` 标记。可以显示带语法高亮和行号的代码、渲染后的 markdown，或者沙箱里的 HTML。标签栏里有复制和下载按钮。

### Terminal
基于 xterm.js 的终端，连接到 agent 工作目录里的 PTY shell（bash/PowerShell）。支持 Nerd Font 字形、窗口缩放和明暗主题。

### Debug（标签页）
四个标签：Logs（通过 WebSocket 实时追 API server 日志）、Trace（工具调用耗时瀑布图）、Prompt（当前 system prompt 及其 diff）、Events（chat store 里所有消息的全量流）。

### Settings（标签页）
七个标签：Session、Tokens、Jobs、Extensions（已安装包）、Triggers（活跃触发器）、Cost（token 成本估算）、Environment（cwd + 打码后的环境变量）。

### Creatures（仅 terrarium）
creature 列表，带状态点和 channel 列表。点某个 creature 会切换聊天标签。

## 拆到单独窗口

在编辑模式下，带 `supportsDetach: true` 的面板可以通过 Pop Out 的 kebab 菜单动作弹到独立窗口。弹出的窗口是一个最小外壳页面，路径是 `/detached/<instanceId>--<panelId>`，会自己连后端。

## 状态栏

底部一直会显示：
- 实例名 + 状态点
- 模型快速切换器（下拉菜单）+ 设置齿轮
- Session id（点击可复制）
- 正在运行的任务数
- 已运行时间

## 技术细节

分割树存的是普通 JSON 结构：
```json
{
  "type": "split",
  "direction": "horizontal",
  "ratio": 70,
  "children": [
    { "type": "leaf", "panelId": "chat" },
    { "type": "split", "direction": "vertical", "ratio": 50,
      "children": [
        { "type": "leaf", "panelId": "activity" },
        { "type": "leaf", "panelId": "state" }
      ]
    }
  ]
}
```

`LayoutNode.vue` 组件是递归的：split 会渲染两个子节点和一条可拖动的分隔条，leaf 则通过 `<component :is>` 渲染面板组件。面板运行时的 props 会通过 Vue 的 provide/inject 从路由页面往下传。

## 另见

- [Serving](serving.md)：通过 `kt web` / `kt app` / `kt serve` 打开仪表盘。
- [Development / Frontend](../dev/frontend.md)：给贡献者看的前端架构说明。
