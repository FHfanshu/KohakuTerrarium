# 模型与预设配置

`llm_profiles.yaml` 里 backends、presets、profiles 到底是什么关系?

## 配置文件在哪

默认位置：

```text
~/.kohakuterrarium/llm_profiles.yaml
```

如果你是 Windows 用户，通常就是：

```text
C:\Users\你的用户名\.kohakuterrarium\llm_profiles.yaml
```

想直接打开这个目录，可以在资源管理器地址栏（ 或者 win+r 跳出的 "运行" 框 ）里输入：

```text
%USERPROFILE%\.kohakuterrarium
```

也可以在 PowerShell 里这样打开：

```powershell
explorer $env:USERPROFILE\.kohakuterrarium
```

## 三层结构

把这三层理解成"服务商 → 模型设置 → 最终配置"就行了：

| 层 | 字段 |你可以理解成 | 存什么 |
|----|------|-------------|--------|
| 第一层 | `backends` | 服务商 | 连到哪家的 API、用什么协议、密钥在哪 |
| 第二层 | `presets` | 模型设置 | 用哪个具体模型、上下文多长、推理力度多大 |
| 第三层 | `profiles` | 合并结果 | 前两层合起来后的完整配置，自动生成 |

**关键点**：`profiles` 不用你管。它是框架自动从 `presets` 合出来的。你只需要配置 `backends` 和 `presets`。

## backends：告诉框架"连哪家服务商"

```yaml
backends:
  my-openai:
    backend_type: openai          # 协议类型
    base_url: https://api.example.com/v1  # API 地址
    api_key_env: MY_API_KEY       # 环境变量名（不是密钥本身）
```

### backend_type 怎么选

`backend_type` 决定框架用什么方式跟服务商通信：

| backend_type | 适用场景 | 说明 |
|--------------|----------|------|
| `openai` | OpenAI、vLLM、Ollama、国产大模型 API | 只要接口兼容 OpenAI 协议（大部分都是），就用这个 |
| `anthropic` | Anthropic 官方 API | 用原生 Anthropic SDK |
| `codex` | ChatGPT 订阅用户 | 用 OAuth 登录，不需要 API key |

**重点**：国产大模型（阿里、百度、智谱、MiniMax、Kimi 等）、本地推理框架（vLLM、Ollama、LM Studio）、以及各类中转 API，只要它们的接口是 OpenAI 兼容格式（`/v1/chat/completions`），都用 `backend_type: openai`。

### 常见服务商配置示例

```yaml
backends:
  # OpenAI 官方
  openai-direct:
    backend_type: openai
    base_url: https://api.openai.com/v1
    api_key_env: OPENAI_API_KEY

  # Anthropic 官方
  anthropic-direct:
    backend_type: anthropic
    base_url: https://api.anthropic.com
    api_key_env: ANTHROPIC_API_KEY

  # 本地 vLLM 或 Ollama
  local-llm:
    backend_type: openai              # OpenAI 兼容协议
    base_url: http://localhost:8000/v1
    api_key_env: LOCAL_LLM_KEY        # 本地的话随便设个值就行

  # 某国产大模型（比如智谱 GLM）
  zhipu:
    backend_type: openai              # OpenAI 兼容
    base_url: https://open.bigmodel.cn/api/paas/v4
    api_key_env: ZHIPU_API_KEY

  # 某中转 API 服务
  proxy-api:
    backend_type: openai
    base_url: https://api.some-proxy.com/v1
    api_key_env: PROXY_API_KEY

  # Codex OAuth（ChatGPT 订阅用户）
  # 不需要 base_url 和 api_key_env，用 kt login codex 登录
```

### api_key_env 注意事项

`api_key_env` 写的是**环境变量的名字**，不是密钥本身。这样做是为了避免把密钥写进配置文件。

实际密钥要设在环境变量里：

```powershell
# PowerShell 临时设置
$env:OPENAI_API_KEY = "sk-..."

# 永久设置
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-...", "User")
```

## presets：告诉框架"用哪个模型、怎么用"

```yaml
presets:
  my-gpt5:
    provider: my-openai     # 引用上面定义的 backend 名
    model: gpt-5.4          # 模型 ID（服务商那边的名字）
    max_context: 1000000    # 最大上下文 token 数
    max_output: 131072      # 最大输出 token 数
    reasoning_effort: high   # 推理力度
    extra_body:             # 传给 API 的额外参数
      thinking:
        type: adaptive
        budget_tokens: 65536
```

- `provider`：填你在 `backends` 里定义的那个名字（比如 `my-openai`）
- `model`：模型的具体名称，要跟服务商那边一致
- `max_context` / `max_output`：限制上下文和输出的长度
- `reasoning_effort`：推理强度（不同厂商参数不一样，后面有表）
- `extra_body`：额外参数，直接传给 API

## 配完怎么用

### 设为默认模型

```powershell
kt model default my-gpt5
```

之后运行 `kt run` 时默认就用这个。

### 临时换个模型

```powershell
kt run @kt-biome/creatures/swe --llm another-preset
```

### 查看当前配置

```powershell
kt model list
kt model show my-gpt5
```

## 推理参数：不同厂商不一样

各家模型的"推理力度"参数格式不同，别搞混：

### OpenAI 系（GPT-5.x）

直接用 `reasoning_effort`：

```yaml
reasoning_effort: medium  # none | low | medium | high | xhigh
```

### Anthropic 系（Claude）

用 `extra_body` 的 `thinking` 参数（2026 年最新格式）：

```yaml
extra_body:
  thinking:
    type: adaptive          # 仅支持 adaptive，旧的 enabled 已废弃
  output_config:
    effort: high            # low | medium | high | xhigh
```

> 注意：旧的 `{type: enabled, budget_tokens: N}` 格式会报 400 错误。请使用 `adaptive + effort` 新格式。

### Google 系（Gemini 3.1 Pro）

Gemini 3.1 Pro 无法关闭 thinking（dynamic thinking 预设开启，模型会自动根据任务复杂度调整推理深度）。

使用 `thinking_config` 配置：

```yaml
extra_body:
  google:
    thinking_config:
      thinking_level: high  # low | medium | high | max
```

- `low`：最快、推理深度较浅，适合简单任务
- `medium`：Gemini 3.1 Pro 新增的平衡层级，速度与推理兼顾
- `high`：预设值，适合大多数复杂任务
- `max`：最高推理深度，适合极端复杂问题，最慢最贵

### 国产大模型（MiMo、GLM、Kimi 等）

大部分用 OpenAI 兼容格式：

```yaml
extra_body:
  reasoning:
    enabled: true
    effort: high
```

具体看各家文档，参数名可能略有不同。

## 常见模型参数速查

| 模型 | 上下文窗口 | 最大输出 | 推理参数格式 |
|------|-----------|----------|-------------|
| GPT-5.4 | 1M | 128K | `reasoning_effort: none/low/medium/high/xhigh` |
| GPT-5.4-mini | 400K | 128K | 同上 |
| Claude Opus 4.7 | 1M | 128K | `thinking: {type: adaptive} + effort`，旧 budget_tokens 已废弃 |
| Claude Opus 4.6 | 1M | 128K | 同上 |
| Claude Sonnet 4.6 | 1M / 200K | 64K~128K | 同上，平衡型，适合大多数任务 |
| Gemini 3.1 Pro | 1M | 64K | `thinking_level: low/medium/high/max`，无法关闭 thinking |
| MiMo-V2-Pro | 1M | 64K | `reasoning.effort` |
| GLM-5.1 | 200K | 128K | `reasoning.enabled + effort`，强 agentic，coding 突出 |
| Kimi K2.5 | 256K | 16K | 原生多模态，内置 thinking mode |

> 注意：上下文窗口 ≠ 模型实际注意力能力。大多数标称 1M 上下文窗口的模型，实际有效注意力范围只有 256K-400K，超过后推理质量会下降。此表信息可能滞后或存在误差，请以各模型官方文档为准。

## 常见问题

### 改了配置没生效

配置改完要重启 creature，或者：

```powershell
kt model list   # 会重新加载配置
```

### 提示 `provider not found`

你在 preset 里写的 `provider` 名字必须跟 `backends` 里定义的完全一致。检查拼写。

### 提示找不到 API key

确认你设了对应的环境变量：

```powershell
# 检查环境变量有没有设
$env:OPENAI_API_KEY

# 没设就设一下
$env:OPENAI_API_KEY = "sk-..."
```

### 模型返回空或报错

1. 先确认 API key 有效
2. 确认 `base_url` 正确（注意末尾有没有 `/v1`）
3. 确认 `backend_type` 选对了：只要是 OpenAI 兼容接口，都用 `openai`

### 用国产大模型怎么配

跟 OpenAI 一样配，只是 `base_url` 换成国产大模型的地址：

```yaml
backends:
  qwen:
    backend_type: openai
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    api_key_env: QWEN_API_KEY

presets:
  qwen-max:
    provider: qwen
    model: qwen-max
    max_context: 32000
```

---

[CLI 与 WebUI 使用 →](cli-webui)