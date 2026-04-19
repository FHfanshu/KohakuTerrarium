# 常见解惑 (FAQ)

## 基础概念

### 如何区分单 Creature (`kt run`) 和 Terrarium (`kt terrarium run`)？它们的 Creature 都是热插拔的吗？

*   **单 Creature (`kt run`)**：
    *   本质上是一个 `Agent` 实例。它通过工具调用（Tool Calling）拉起 Sub-agent（子智能体）来分解任务。
    *   这是垂直层级的调用，属于阻塞式的临时会话，**没有热插拔**的概念。
*   **Terrarium (`kt terrarium run`)**：
    *   本质上是一个纯粹的连线层和运行时。它管理多个平行的 Creature，提供共享环境和通信频道（Channels）。
    *   **只有 Terrarium 中的 Creature 支持热插拔**（内部通过 `HotPlugMixin` 实现）。你可以在运行期间动态添加、移除 Creature 或频道，并重新进行连线，而无需重启整个系统。
