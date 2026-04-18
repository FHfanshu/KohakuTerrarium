# Root agent

## 它是什么

**Root agent** 是一个放在 terrarium *外面* 的 creature，在 terrarium 里代表用户。结构上它就是普通 creature：配置一样，模块一样，生命周期也一样。之所以叫 "root"，是因为：

1. 它在团队外面——用户和 root 说话，root 再和 terrarium 交互。
2. 它会自动拿到 **terrarium 管理工具集**（`terrarium_create`、`terrarium_send`、`creature_start`、`creature_stop`、`creature_status`、`terrarium_status` 等）。
3. 它会自动监听所有共享 channel，并接收专用的 `report_to_root` 队列。

## 它为什么存在

只有 terrarium 的话，它本身没有对话入口：一组 creatures 通过 channels 协作，但没人来驱动它们。这种形式适合一些后台流程。可一旦是交互场景，人需要有一个固定对象可以直接对话。root 就是这个对象。

理论上，你也可以用一个普通 creature 再手动把工具集和监听关系接好。但每次都要自己配，麻烦，也容易漏。把 `root` 作为 terrarium 配置里的一级位置，省掉了这部分样板。

## 怎么定义

```yaml
terrarium:
  root:
    base_config: "@kt-defaults/creatures/root"
    controller:
      llm: gpt-5.4
      reasoning_effort: high
  creatures:
    - ...
  channels:
    - ...
```

agent 配置里合法的内容，都可以放进 `root:`。继承（`base_config`）的行为也一样。运行时只有这几点不同：

- terrarium runtime 会把管理工具集注入它的 registry。
- 它会自动监听每个 creature channel，所以能看到全部活动。
- 用户直接和它交互（TUI / CLI / web）。

## 怎么实现

`terrarium/factory.py:build_root_agent` 会在 creatures 构建完之后调用。它用共享环境创建 root（这样管理工具才能看到 creatures 和 channels），把 `TerrariumToolManager` 注册进它的 registry，再把输出接回用户传输层。

root 会先被构建出来，但不会立刻启动；要等用户真的开始和 terrarium 交互，它才启动。这样 `kt terrarium run` 可以先显示团队状态，再唤醒 root。

## 所以你可以做什么

- **面向用户的调度者。** 用户对 root 说“让 SWE 修掉 auth bug，再让 reviewer 审掉”。root 通过 channels 发消息，并监听 `report_to_root` 来判断是否完成。
- **动态组队。** root 可以按当前任务 `creature_start` 新的 specialist，用完后再 `creature_stop`。
- **启动和管理 terrarium。** root agent 自己也可以通过 `terrarium_create` 创建并管理*其他* terrariums。
- **观测入口。** 因为 root 会自动监听所有内容，适合把 summarisation plugin、告警规则之类的东西挂在这里。

## 不要被限制

没有 root 的 terrarium 完全成立——比如无头流水线、cron 驱动的协作、批处理任务。root 只是为交互场景提供方便。

另外，root 依然“只是一个 creature”。你能用在普通 creature 上的模式，放到 root 上也一样可用，比如交互式 sub-agent、plugins、自定义 tools。

## 另见

- [Terrarium](/concepts/multi-agent/terrarium.md)（英文）——root 所在的那一层。
- [Multi-agent overview](/concepts/multi-agent/README.md)（英文）——root 在整体模型里的位置。
- [reference/builtins.md — terrarium_* tools](/reference/builtins.md)（英文）——管理工具集。
