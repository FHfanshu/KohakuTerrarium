# 模型与预设配置



这篇讲清楚一个很多人搞混的事：`llm_profiles.yaml` 里 backends、presets、profiles 到底是什么关系。

## 三层结构

用一个比喻就明白了：

| 层 | 字段 | 比喻 | 存什么 |
|----|------|------|--------|
| 第一层 | `backends` | 电话号码簿 | 怎么连到服务器（地址、密钥名、协议类型） |
| 第二层 | `presets` | 联系人名片 | 用哪个模型、上下文多长、推理力度多大 |
| 第三层 | `profiles` | 运行时配置 | 把 preset 和 backend 合并后的完整信息 |

**关键点**：`profiles` 是 `presets` 的镜像，框架每次保存都会同步。你只需要关注 `backends` 和 `presets` 就行。

## backends：连接信息

```yaml
backends:
  my-openai:
    backend_type: openai          # 协议类型：openai | anthropic | codex
    base_url: https://api.example.com/v1  # API 地址
    api_key_env: MY_API_KEY       # 环境变量名（不是密钥本身）
```

- `backend_type`：决定用什么客户端连。`openai` 适用于所有 OpenAI 兼容接口，`anthropic` 用原生 Anthropic SDK，`codex` 用 OAuth 认证。
- `api_key_env`：只写环境变量名。实际密钥放在环境变量里，不写进配置文件。

## presets：模型配置

```yaml
presets:
  my-gpt5:
    provider: my-openai     # 引用上面定义的 backend 名
    model: gpt-5.4          # 模型 ID
    max_context: 1000000    # 最大上下文 token 数
    max_output: 131072      # 最大输出 token 数
    reasoning_effort: high   # 推理力度
    extra_body:             # 传给 API 的额外参数
      thinking:
        type: adaptive
        budget_tokens: 65536
```

## 怎么配自己的模型

### 第一步：设 backend

举几个常见例子：

```yaml
backends:
  # OpenAI 直连
  openai-direct:
    backend_type: openai
    base_url: https://api.openai.com/v1
    api_key_env: OPENAI_API_KEY

  # Anthropic 直连
  anthropic-direct:
    backend_type: anthropic
    base_url: https://api.anthropic.com
    api_key_env: ANTHROPIC_API_KEY

  # 本地 vLLM / Ollama
  local-llm:
    backend_type: openai
    base_url: http://localhost:8000/v1
    api_key_env: LOCAL_LLM_KEY

  # Codex OAuth（ChatGPT 订阅）
  # 不需要 base_url 和 api_key_env
```

### 第二步：设 preset

```yaml
presets:
  my-gpt5:
    provider: openai-direct
    model: gpt-5.4
    max_context: 1000000
    max_output: 131072
    reasoning_effort: high
```

### 第三步：设为默认模型

```powershell
kt model default my-gpt5
```

## 推理参数速查

不同模型的推理参数格式不一样，别搞混了：

### OpenAI 系（GPT-5.4 等）

用 `reasoning_effort`：

```yaml
reasoning_effort: medium  # none | low | medium | high | xhigh
```

或 `extra_body`：

```yaml
extra_body:
  reasoning:
    enabled: true
    effort: high
```

### Anthropic 系（Claude 等）

用 `extra_body` 的 thinking 参数：

```yaml
extra_body:
  thinking:
    type: adaptive        # 启用自适应思考
    budget_tokens: 65536  # 思考 token 预算
```

effort 级别：`low | medium | high | max`

### Google 系（Gemini 等）

用 `extra_body` 的 Google 专用参数：

```yaml
extra_body:
  google:
    thinking_config:
      thinking_level: HIGH  # LOW | MEDIUM | HIGH
```

### 其他模型（MiMo、GLM、Kimi 等）

大部分 OpenAI 兼容接口用：

```yaml
extra_body:
  reasoning:
    enabled: true
    effort: high
```

## 常见模型参数参考

| 模型 | 上下文窗口 | 最大输出 | 推理参数 |
|------|-----------|----------|----------|
| **GPT-5.4** | 1,000K | 128K | `reasoning_effort`: none/low/medium/high/xhigh |
| **GPT-5.4-mini** | 400K | 128K | 同上 |
| **GPT-5.4-nano** | 400K | 128K | 同上 |
| **GPT-5.3-codex** | 272K | 128K | 同上 |
| **Claude Opus 4.6** | 1,000K | 128K | `thinking: {type: adaptive, budget_tokens}` |
| **Claude Sonnet 4.6** | 1,000K | 64K | 同上 |
| **Claude Haiku 4.5** | 200K | 64K | 不支持 extended thinking |
| **Gemini 3.1 Pro** | 1,000K | 64K | `thinking_level`: LOW/MEDIUM/HIGH |
| **Gemini 3 Flash** | 1,000K | 64K | 同上 |
| **MiMo-V2-Pro** | 1,000K | 64K | `reasoning_effort`: low/medium/high |
| **GLM-5** | 256K | 16K | `reasoning.enabled+effort` |
| **Kimi K2.5** | 256K | 16K | 内置 thinking，`reasoning.enabled` |
| **MiniMax M2.7** | 200K | 16K | `thinking: {type: adaptive}` |
| **MiniMax M2.5** | 197K | 16K | 同上 |

> 注意：上下文窗口是模型理论最大值。Codex OAuth 等某些渠道可能有更低的实际限制（如 GPT-5.4 只给 272K budget） 而且上下文窗口大小不等于模型实际注意力能力范围。

## 配置文件在哪

```text
~/.kohakuterrarium/llm_profiles.yaml
```

手动编辑也行，用命令也行：

```powershell
# 登录 provider
kt login openai
kt login codex

# 切换默认模型 (如模型配置项存在)
kt model default gpt-5.4
kt model default claude-4-6-sonnet

# 查看当前配置
kt model show
kt model list
```

## 常见问题

### 改了配置没生效

配置文件改完后需要重启 creature。或者：

```powershell
# 重新加载
kt model list
```

### `provider not found`

preset 里写的 `provider` 名字必须和 backends 里定义的一致。检查拼写。

### `api_key_env` 找不到

确保你设了对应的环境变量：

```powershell
# PowerShell 临时设置
$env:OPENAI_API_KEY = "sk-..."

# 或者永久设置
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-...", "User")
```

### 模型返回空或报错

1. 先确认 API key 有效
2. 确认 base_url 正确
3. 确认 backend_type 选对了（OpenAI 兼容接口一律用 `openai`）

---

