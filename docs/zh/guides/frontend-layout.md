# 前端布局

这篇是写给两种人看的：一种是平时用 `kt web` / `kt app` / `kt serve` 打开这个 Web 仪表盘的人，另一种是想自己改界面布局的人。

先用一句人话讲明白：这个仪表盘不是写死的固定排版，本质上是一套“能切成两半、再继续切”的布局系统。屏幕上的每一块，要么就是一个真正显示内容的面板，要么就是一个“分割节点”，负责把空间继续拆成两块，中间那条分隔线还能直接拖。你切换 preset 的时候，会直接把整套布局一下子换掉；进编辑模式的时候，则是在当前这套布局上原地改。

如果你还不知道这个仪表盘是怎么打开的，先看一下 [Serving](serving.md)。那篇讲的是 `kt web`、`kt app`、`kt serve` 分别怎么用。

## 核心概念

先把几个词说清楚，不然后面容易看晕。

- **Panel（面板）**：可以理解成界面里一块“专门干一件事”的区域。比如 Chat 聊天、Files 文件、Activity 活动、State 状态、Canvas、Debug、Settings、Terminal 这些，都算 panel。代码里这些 panel 会注册在 `stores/layoutPanels.js`，系统靠 id 去找到它们。
- **Split tree（分割树）**：这个词听着有点学术，其实意思很简单，就是“整个界面怎么切”的那棵树。每个节点只有两种可能：
  - 要么是 **leaf（叶子）**，也就是这里直接放一个面板；
  - 要么是 **split（分割）**，也就是把这一块区域再分成左右两块，或者上下两块，中间带一条能拖的分隔线。
- **Preset（预设布局）**：就是一整套已经配好的布局方案，而且它有名字。你切换 preset，等于把整棵布局树整个换掉。preset 既可以是系统自带的，也可以是你自己另存的新布局。
- **Header（顶部栏）**：页面最上面那一条。里面一般会放实例信息、preset 下拉框、编辑布局按钮、Ctrl+K 命令面板入口，还有停止按钮。
- **Status bar（状态栏）**：页面最下面那一条。主要显示模型切换器、session id、当前任务数量、运行时间这些信息。

## 默认预设布局

系统自带几套常用布局，直接按快捷键就能切。

| 快捷键 | Preset | 布局大概长什么样 |
|--------|--------|------------------|
| Ctrl+1 | Chat Focus | chat \\| status-dashboard（上）+ state（下） |
| Ctrl+2 | Workspace | files \\| editor+terminal \\| chat+activity |
| Ctrl+3 | Multi-creature | creatures \\| chat \\| activity+state |
| Ctrl+4 | Canvas | chat \\| canvas+activity |
| Ctrl+5 | Debug | chat+state（上）/ debug（下） |
| Ctrl+6 | Settings | settings（全屏） |

再补一句默认行为：

- 如果当前实例是 **creature**，页面会默认帮你选 **Chat Focus**。
- 如果当前实例是 **terrarium**，页面会默认帮你选 **Multi-creature**。
- 你每个实例上一次用的是哪套 preset，会记在 `localStorage` 里。也就是说，下次再打开，通常会接着你上次那套来。

## 编辑模式

想改布局，按 **Ctrl+Shift+L**，或者直接点顶部栏里的编辑按钮，就能进编辑模式。

进来以后，你会发现每个面板上面多出一条偏琥珀色的操作条。别被术语吓到，它其实就是“这块怎么改”的快捷工具栏。里面通常有这些按钮：

- **Replace**：把当前这块直接换成别的 panel。点下去会弹一个选择器，你从已注册的 panel 里挑一个就行。
- **Split H / Split V**：把当前这块一分为二。
  - `Split H` 一般就是左右分；
  - `Split V` 一般就是上下分。
  分完以后会多出一个新的空槽位，你可以再往里塞 panel。
- **Close**：把当前 panel 关掉。关掉以后，这块空间不会空着不管，而是让它旁边那个兄弟节点把空间接过去。
- **+ Add panel**：如果某个槽位现在还是空的，就会看到这个按钮，点它可以往空位里加面板。

页面上方还会多出一条“编辑模式横幅”，上面一般有这几个动作：

- **Save**：保存当前修改。
  - 但注意，只能保存到**用户自己的 preset**；
  - 系统内置 preset 不能直接覆盖。
- **Save as new**：把你现在这套布局另存成一个新的用户 preset，名字你自己取。
- **Revert**：把这次改动全扔掉，回到原来的布局。
- **Exit**：退出编辑模式。如果你改了但还没存，系统会先提醒你，防止你手一滑白改了。

这里有个挺关键的实现细节，但也很好懂：

你在编辑模式里改的是 preset 的一个**深拷贝**，不是那份“原件”。所以只要你还没点保存，原来的布局其实一直都没动。这也是为什么你可以放心乱试，试完不满意再 Revert。

## 键盘快捷键

常用快捷键就这几个：

| 快捷键 | 作用 |
|--------|------|
| Ctrl+1..6 | 切到对应 preset |
| Ctrl+Shift+L | 打开/关闭编辑模式 |
| Ctrl+K | 打开命令面板 |
| Esc | 退出编辑模式 |

有两个小细节值得提一下：

- **Ctrl+K** 比较强势，就算你当前光标在输入框里，它也照样会触发。
- 但 **preset 的快捷键** 会更克制一点：如果你正在文本输入框或者 textarea 里打字，它就不会硬抢按键，免得你一边输入一边把布局切飞了。

## 命令面板

按 **Ctrl+K** 就能打开命令面板。

它会把所有已注册命令拿来做模糊匹配，所以你不用每次都打得特别完整，输个大概也能搜出来。常见项大概有这些：

- `Mode: <preset>`：切换到某个 preset
- `Panel: <panel>`：把某个 panel 加到它默认偏好的区域
- `Layout: edit / save as / reset`：布局相关操作
- `Debug: open logs`：打开日志

另外它还有一套“前缀分流”规则，也就是你输入的第一个符号，会影响它按什么类型去理解：

- `>`：命令，默认就是这个
- `@`：mentions
- `#`：sessions
- `/`：slash commands

你可以把它理解成一个总入口：同一个面板里，根据前缀切不同频道。

## 各个面板到底是干嘛的

下面这部分就按 panel 一个个说人话。

### Chat

这个就是主聊天区，也是你最常待的地方。

它不只是简单显示对话，还支持这些东西：

- 改一条消息再重跑
- 重新生成回复
- 把工具调用折叠/展开来看
- 子 agent 的嵌套显示

如果你平时主要是在跟 agent 对话、看它调工具，那基本就是盯着这个面板。

### Activity（标签页）

这是个带 tab 的面板，里面有三个标签：

- **Session**：看 session 相关信息，比如 id、cwd、creatures/channels
- **Tokens**：看 token 输入、输出、缓存这些数据，还有上下文条，以及 compact 阈值之类的信息
- **Jobs**：看当前正在跑的工具调用，还能直接点停止

说白了，Activity 更像“这个实例现在在干嘛”的实时观察区。

### State（标签页）

这个也是 tab 面板，一共有四个标签：

- **Scratchpad**：agent 工作记忆里的键值对，你可以理解成它临时记在小本本上的东西
- **Tool History**：这个 session 里所有工具调用的历史记录
- **Memory**：对 session 事件做 FTS5 搜索
- **Compaction**：上下文压缩的历史

如果你想看 agent 脑子里现在大概记了什么、调过哪些工具、上下文怎么被压缩过，这块就很有用。

### Files

这是文件树面板。

除了正常浏览文件，它还有刷新功能；另外还有个 **Touched** 视图，会把 agent 读过、写过、或者出错过的文件按动作分组列出来。

这个设计很实用，因为你不用自己满项目翻，就能快速看到“刚才 agent 动过哪些文件”。

### Editor

这是编辑器面板，用的是 Monaco。

你会看到这些常见能力：

- 文件 tab
- 未保存标记
- `Ctrl+S` 保存

如果打开的是 markdown 文件（比如 `.md`、`.markdown`、`.mdx`），还能在两种模式之间切：

- **Monaco**：偏代码编辑模式
- **Vditor**：偏所见即所得的富文本 markdown 编辑，带工具栏、数学公式、代码块支持

所以它不只是写代码，也照顾到了文档编辑场景。

### Canvas

Canvas 会自动识别 assistant 消息里的两类东西：

- **长代码块**（15 行以上）
- `##canvas##` 标记

识别到以后，它可以把内容用更适合展示的方式放出来，比如：

- 带语法高亮和行号的代码
- 渲染后的 markdown
- 沙箱中的 HTML

而且在标签栏上还有复制、下载按钮。你可以把它理解成“专门拿来展示大块输出内容”的区域，特别适合代码、文档片段、HTML 预览这种东西。

### Terminal

这是终端面板，基于 xterm.js。

它连的是 agent 工作目录里的 PTY shell，具体可能是 bash，也可能是 PowerShell。支持的体验包括：

- Nerd Font 图标字形
- 窗口 resize
- 明亮 / 深色主题

简单讲，就是你可以直接在 UI 里开终端，不用再切出去。

### Debug（标签页）

这是调试面板，也分 tab，一共有四个：

- **Logs**：通过 WebSocket 实时追 API server 日志
- **Trace**：工具调用耗时的瀑布图
- **Prompt**：当前 system prompt，以及它的 diff
- **Events**：chat store 里所有消息的全量流水

如果你在查问题、盯性能、看 prompt 到底变成了什么，这块会特别有用。

### Settings（标签页）

设置面板同样是 tab 结构，一共有七个标签：

- Session
- Tokens
- Jobs
- Extensions（已安装扩展/包）
- Triggers（当前活跃的触发器）
- Cost（token 成本估算）
- Environment（cwd 和打码后的环境变量）

所以它不只是“改配置”的地方，也有不少偏查看状态、查看环境信息的内容。

### Creatures（仅 terrarium）

这个面板只在 terrarium 场景下出现。

里面会列出 creature 列表、状态点、channel 列表。你点某个 creature，就能切到对应的聊天标签。

如果你是在多 creature 的环境里工作，这块基本就是你的总控面板。

## 把面板弹到独立窗口

有些 panel 支持从主界面里“弹出去”，变成单独窗口。

具体来说，在编辑模式下，如果某个 panel 带了 `supportsDetach: true`，你就可以通过那个 kebab 菜单里的 **Pop Out** 动作把它拆出来。

拆出去以后，系统会开一个最小壳子的独立页面，地址长这样：

`/detached/<instanceId>--<panelId>`

这个独立窗口会自己去连后端，不是简单把原页面 iframe 一下。所以你可以把某些需要单独盯着看的 panel，比如日志、终端之类，单独拎出去放另一个显示器上。

## 状态栏

状态栏一直固定在底部，属于那种你低头一眼就能扫到的信息区。它一般会显示：

- 实例名 + 状态点
- 模型快速切换器（下拉框）+ 设置齿轮
- Session id（点一下可复制）
- 正在运行的任务数
- 已经跑了多久

它的作用就是让你不用来回切面板，也能随时知道这个实例当前大概是什么状态。

## 技术细节

如果你关心底层到底怎么存布局，这里给你看个真相：它其实就是普通 JSON。

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

这个例子翻成人话就是：

- 先把整体横着分成左右两块；
- 左边 70% 放 chat；
- 右边再竖着切成上下两块；
- 上面放 activity，下面放 state。

界面里的 `LayoutNode.vue` 是个递归组件。

意思就是：

- 如果当前节点是 **split**，它就继续渲染两个子节点，再加一条可拖动的分隔线；
- 如果当前节点是 **leaf**，它就通过 `<component :is>` 去渲染对应的 panel 组件。

至于 panel 运行时要用到的 props，则是从路由页面通过 Vue 的 `provide/inject` 一路往下传。

## 另见

- [Serving](serving.md) —— 讲怎么通过 `kt web` / `kt app` / `kt serve` 打开仪表盘。
- [Development / Frontend](./dev/frontend.md) —— 给贡献者看的前端架构说明。
