---
name: think
description: Explicit reasoning step preserved in context
category: builtin
tags: [reasoning, planning]
---

# think

Explicit reasoning/thinking step. The tool itself does nothing --
its value is that the thought is preserved in conversation context
and won't be lost to context compaction.

Use this to externalize multi-step reasoning, plan before acting,
or record decisions that should survive context compaction.

## Arguments

| Arg | Type | Description |
|-----|------|-------------|
| thought | string | Your reasoning (required) |

## WHEN TO USE

- Before complex multi-step tasks
- When you need to plan your approach
- To record analysis or decisions
- When reasoning through tradeoffs

## Output

Returns "Noted." (fixed response).

## LIMITATIONS

- No side effects (the tool does nothing except preserve the thought in context)
- Subject to context compaction like all other messages (but prioritized for retention)

## TIPS

- Use before starting complex tasks
- Structure your thoughts with numbered steps
- Record key decisions and their reasoning
