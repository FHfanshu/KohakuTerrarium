# Memory

给想搜索过去 session 事件的人看。无论你是在 CLI 里查、在 Python 里查，还是让 agent 在运行时自己查，都是这一套。

session 的事件日志本身也可以当一个本地小型知识库。给它建好搜索索引后，就能用 FTS 做关键词搜索（免费，速度快），也能做语义搜索（需要 embedder），或者做混合搜索：先用关键词召回，再按 embedding 相似度重排。agent 还能通过内置的 `search_memory` tool 搜自己或别的 session 的 memory。

概念预读：[memory and compaction](/concepts/modules/memory-and-compaction.md)（英文）、[sessions](/guides/sessions.md)（英文）。

## 可以搜索什么

`~/.kohakuterrarium/sessions/*.kohakutr` 里的每个事件都会变成一个可搜索的“块”：用户输入、assistant 文本、tool call、tool result、子 agent 输出、channel 消息。块会按处理轮次分组，所以搜索结果能带回当时的上下文。

搜索会返回 `SearchResult` 记录，包含这些字段：

- `content` — 命中的文本
- `agent` — 由哪个 creature 产出
- `block_type` — `text` / `tool` / `trigger` / `user`
- `round_num`, `block_num` — 在 session 里的位置
- `score` — 匹配分数
- `ts` — 时间戳

## Embedding provider

一共三类 provider，按你的环境选：

| Provider | 需要什么 | 说明 |
|---|---|---|
| `model2vec`（默认） | 不需要 torch，纯 NumPy | 非常快，安装也最轻。做贴近关键词的检索已经够用，但长文本语义搜索会弱一些。 |
| `sentence-transformer` | `torch` | 慢一些，但语义质量明显更好。也适合 GPU。 |
| `api` | 网络 + API key | 远程 embedder，比如 OpenAI、Jina、Gemini。质量最好，按调用付费。 |
| `auto` | — | 如果能用 API，优先选 `jina-v5-nano`，否则回退到 `model2vec`。 |

预设模型名（可跨 provider 使用）：

- `@tiny` — 最小、最快
- `@base` — 默认平衡点
- `@retrieval` — 针对检索调过
- `@best` — 质量最高
- `@multilingual`, `@multilingual-best` — 适合非英文 session
- `@science`, `@nomic`, `@gemma` — 专用模型

也可以直接传 Hugging Face 路径。

## 建索引

```bash
kt embedding ~/.kohakuterrarium/sessions/swe.kohakutr
```

显式指定参数：

```bash
kt embedding swe.kohakutr \
  --provider sentence-transformer \
  --model @best \
  --dimensions 384
```

`--dimensions` 是 Matryoshka 截断。模型支持的话，可以在生成时直接把向量缩短。

支持增量更新：再次运行 `kt embedding` 时，只会索引新事件。

## 在 CLI 里搜索

```bash
kt search swe "auth bug"                # auto 模式（有向量就用 hybrid，否则用 fts）
kt search swe "auth bug" --mode fts     # 只做关键词搜索
kt search swe "auth bug" --mode semantic
kt search swe "auth bug" --mode hybrid
kt search swe "auth bug" --agent swe -k 5
```

几种模式：

- **`fts`** — 基于 FTS5 的 BM25。不需要 embedding。最快，适合查字面短语。
- **`semantic`** — 纯向量相似度。需要索引。适合查同义改写。
- **`hybrid`** — 先用 BM25 找候选，再按向量相似度重排。两者都可用时，这是默认模式。
- **`auto`** — 自动选当前 session 支持的最强模式。

`-k` 用来限制返回条数。`--agent` 可以把结果限制到 terrarium session 里的某个 creature。

## 让 agent 自己搜索

内置的 `search_memory` tool 用的就是同一套引擎，controller 可以直接调用：

```yaml
# creatures/my-agent/config.yaml
tools:
  - read
  - write
  - search_memory
memory:
  embedding:
    provider: model2vec
    model: "@base"
```

当 LLM 调用 `search_memory` 时，这个 tool 会在*当前* session 的索引上执行。这就是 seamless memory 的基础能力：agent 不用额外搭 RAG 流程，也能回头查自己或队友前几轮说过什么。

tool 参数长这样；具体语法取决于你的 `tool_format`，下面是默认的 bracket 格式：

```
[/search_memory]
@@query=auth bug
@@mode=hybrid
@@k=5
@@agent=swe
[search_memory/]
```

如果你要对*外部*数据源做 RAG，就自己写一个 custom tool，或者写一个会调用向量库的 [prompt plugin](/guides/plugins.md)（英文）。

## 在 creature 里配置 memory

```yaml
memory:
  embedding:
    provider: model2vec       # 或 sentence-transformer、api、auto
    model: "@retrieval"       # 预设名或 HF 路径
```

配了这段后，agent 会在事件写入时自动建索引，不需要再手动跑 `kt embedding`。没配的话，session 不会生成 embedding，但仍然可以做 FTS 搜索。

## 用代码查看

```python
from kohakuterrarium.session.store import SessionStore
from kohakuterrarium.session.memory import SessionMemory
from kohakuterrarium.session.embedding import GeminiEmbedder

store = SessionStore("~/.kohakuterrarium/sessions/swe.kohakutr")
embedder = GeminiEmbedder("gemini-embedding-004", api_key="...")
memory = SessionMemory(store.path, embedder=embedder, store=store)

memory.index_events("swe")
results = await memory.search("refactor", mode="hybrid", k=5)
for r in results:
    print(f"{r.agent} r{r.round_num}: {r.content[:120]} ({r.score:.2f})")

store.close()
```

## 排错

- **`No vectors in index`。** 你用了 `--mode semantic`，但还没先跑 `kt embedding`。先建索引，或者改用 `--mode fts`。
- **`kt embedding` 很慢。** `sentence-transformer` 默认吃 CPU。装带 CUDA 的 torch，或者改用 `model2vec`。
- **provider 安装失败。** `kt embedding --provider model2vec` 没有原生依赖，基本哪都能跑。`sentence-transformer` 需要 `torch`；`api` 需要对应 provider 的 SDK，比如 `openai`、`google-generativeai`。
- **hybrid 模式结果很杂。** 把 `-k` 调低。查询里如果改写很多，优先用 `semantic`；如果查的是字面短语，优先用 `fts`。
- **`search_memory` 查不到东西。** 可能是 session 没配 embedding，或者 session 在你加 memory 配置之前就开始了。这种情况重跑一次 `kt embedding`。

## 另见

- [Sessions](/guides/sessions.md)（英文）— memory 所依赖的 `.kohakutr` 格式。
- [Plugins](/guides/plugins.md)（英文）— seamless memory 的插件模式（`pre_llm_call` 检索）。
- [Reference / CLI](/reference/cli.md)（英文）— `kt embedding`、`kt search` 的参数。
- [Concepts / memory and compaction](/concepts/modules/memory-and-compaction.md)（英文）— 设计原因。