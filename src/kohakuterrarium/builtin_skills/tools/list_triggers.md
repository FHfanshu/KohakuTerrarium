---
name: list_triggers
description: List all active triggers (channel watchers, timers, etc.)
category: builtin
tags: [triggers, introspection]
---

# list_triggers

List all active triggers on this agent.

## Arguments

None.

## Behavior

- Returns all triggers currently registered on the agent.
- Shows each trigger's ID, type, running status, and creation time.
- Includes triggers from terrarium_observe, channel communication, timers,
  and any dynamically created triggers.

## WHEN TO USE

- To see what the agent is currently listening for
- Before creating a new trigger (to avoid duplicates)
- To find trigger IDs for use with `stop_task`
- Debugging why the agent is or isn't responding to events

## Output

```
Active triggers (3):
  observe_team_results (ChannelTrigger) [running] since 14:30:15
  timer_check (TimerTrigger) [running] since 14:28:00
  channel_inbox (ChannelTrigger) [running] since 14:25:30
```

Or "No active triggers." if none are registered.

## TIPS

- Use `stop_task` with a trigger ID to remove a trigger.
- Triggers set up by the terrarium runtime are listed here too.
