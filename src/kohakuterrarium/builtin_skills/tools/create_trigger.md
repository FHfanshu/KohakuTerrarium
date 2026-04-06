---
name: create_trigger
description: Create a trigger (timer, scheduler, channel). Use info tool to read docs first.
category: builtin
tags: [triggers, automation]
---

# create_trigger

Create a trigger dynamically at runtime. Triggers fire events that
wake the agent without user input.

## Arguments

| Arg | Type | Description |
|-----|------|-------------|
| trigger_type | string | Trigger class: TimerTrigger, SchedulerTrigger, or ChannelTrigger (required) |
| trigger_id | string | Unique ID for this trigger (optional, auto-generated if omitted) |
| config | object | Trigger configuration (required, varies by type -- see below) |

## Trigger Types

### TimerTrigger

Fire at regular intervals.

```json
{
  "trigger_type": "TimerTrigger",
  "config": {
    "interval": 300,
    "prompt": "Check status every 5 minutes"
  }
}
```

Config fields:
- `interval` (float, required): seconds between fires
- `prompt` (string): message content when trigger fires
- `immediate` (bool): fire immediately on creation (default: false)

### SchedulerTrigger

Fire at specific clock times.

```json
{
  "trigger_type": "SchedulerTrigger",
  "config": {
    "every_minutes": 30,
    "prompt": "Half-hour check"
  }
}
```

Config fields (pick ONE schedule type):
- `every_minutes` (int): fire every N minutes (aligned to clock)
- `daily_at` (string): fire once per day at "HH:MM" (24h format)
- `hourly_at` (int): fire every hour at minute :MM (0-59)
- `prompt` (string): message content when trigger fires

### ChannelTrigger

Watch a named channel for messages.

```json
{
  "trigger_type": "ChannelTrigger",
  "config": {
    "channel_name": "results",
    "prompt": "New result: {content}"
  }
}
```

Config fields:
- `channel_name` (string, required): channel to watch
- `subscriber_id` (string, optional): ID for broadcast subscriptions
- `prompt` (string, optional): template with {content} substitution
- `filter_sender` (string, optional): only fire for this sender
- `ignore_sender` (string, optional): skip this sender (auto-set to self)

## Notes

- Triggers persist across resume (saved to session store).
- Use `list_triggers` to see active triggers.
- Use `stop_task` to remove a trigger by ID.
- Self-messages are automatically filtered for channel triggers.
- All trigger types are resumable (survive session resume).
