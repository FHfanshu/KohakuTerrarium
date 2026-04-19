# Root agent

## 它是什么

**Root agent** 是一个放在 terrarium *外面* 的 creature，在 terrarium 里代表用户。结构上，它就是另一个 creature：配置一样，模块一样，生命周期也一样。它之所以叫 root，区别在这三点：

1. 它在团队外面。用户和 root 说话，root 再和 terrarium 交互。
2. 它会自动拿到 **terrarium-management toolset**（`terrarium_create`、`terrarium_send`、`creature_start`、`creature_stop`、`creature_status`、`terrarium_status` 等）。
3. 它会自动监听所有 shared channels，并接收专用的 `report_to_root` queue。

## 它为什么存在

一个裸 terrarium 是没有对话入口的：里面的 creatures 会通过 channels 协作，但没有谁来驱动。这对某些后台工作流没问题。可一旦是交互场景，人总得有一个固定对象可以直接对话。root 就是这个对象。

理论上，你也可以拿一个普通 creature，再手动把工具集和监听关系接好。但每次都这样配，很烦，也容易漏。把 `root` 变成 terrarium 配置里的一个一等位置，就是为了省掉这些样板。

## 我们怎么定义它

```yaml
terrarium:
  root:
    base_config: "@kt-biome/creatures/general"
    system_prompt_file: prompts/root.md     # 和这个团队放在一起的委派 prompt
    controller:
      reasoning_effort: high
  creatures:
    - ...
  channels:
    - ...
```

agent 配置里合法的内容，都可以放进 `root:`。继承（`base_config`）的行为也一样。

补一句写法上的约定：kt-biome **没有**提供一个通用的 `root` creature。每个 terrarium 自己带自己的 `root:` 配置块，以及旁边那份 `prompts/root.md`。这样 prompt 就可以直接写团队内部的真名字，比如“写代码就发给 `driver`”，读起来会比“发给那个 SWE creature”自然很多。剩下的通用能力都由框架补上。

无论你在配置里怎么写，运行时 root 都会被框架额外做这几件事：

- terrarium runtime 会把管理工具集（`terrarium_create`、`terrarium_send`、`creature_start`、`creature_stop`、`creature_status`、`terrarium_status` 等）注入它的 registry。
- 它会自动监听每个 creature channel，所以能看到全部团队活动。
- 框架会自动生成一段“terrarium 感知”prompt，列出这个 terrarium 里绑定了哪些 creatures 和 channels，并追加到 root 的 system prompt 后面。
- 用户直接和它交互（TUI / CLI / web）。

所以你的 `prompts/root.md` 主要只需要写委派风格、团队口吻这些内容；团队拓扑认知由框架自动提供。

## 我们怎么实现它

`terrarium/factory.py:build_root_agent` 会在 creatures 构建完之后调用。它用 shared environment 创建 root，这样管理工具才能看到 creatures 和 channels；然后把 `TerrariumToolManager` 注册进它的 registry，再把输出接回用户传输层。

root 会先被构建出来，但不会立刻启动。要等用户真的开始和 terrarium 交互，它才启动。这样 `kt terrarium run` 可以先显示团队状态，再唤醒 root。

## 所以你可以做什么

- **面向用户的调度者。** 用户对 root 说“让 SWE 修掉 auth bug，再让 reviewer 批掉”。root 通过 channels 发消息，并监听 `report_to_root` 看有没有完成。
- **动态组队。** root 可以按当前任务 `creature_start` 新的 specialist，用完后再 `creature_stop`。
- **启动和管理 terrarium。** root agent 自己也可以通过 `terrarium_create` 创建并管理*其他* terrariums。
- **观测入口。** 因为 root 会自动监听所有内容，适合把 summarisation plugins、告警规则之类的东西挂在这里。

## 别把它想死了

没有 root 的 terrarium 完全成立，比如无头流水线、cron 驱动的协作、批处理任务。root 只是给交互场景省事。

另外，root 归根到底还是“一个 creature”。普通 creature 能用的模式，放到 root 上也一样能用，比如交互式 sub-agents、plugins、自定义 tools。

## 另见

- [Terrarium](terrarium.md) —— root 所在的那一层。
- [多智能体概览](README.md) —— root 在整体模型里的位置。
- [builtins 参考：terrarium_* tools](../../reference/builtins.md) —— 管理工具集。
