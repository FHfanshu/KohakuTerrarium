"""Create trigger tool: dynamically create triggers at runtime."""

from typing import Any

from kohakuterrarium.builtins.tools.registry import register_builtin
from kohakuterrarium.modules.tool.base import (
    BaseTool,
    ExecutionMode,
    ToolContext,
    ToolResult,
)
from kohakuterrarium.utils.logging import get_logger

logger = get_logger(__name__)

# Registry of universal trigger types (type_name -> class)
_TRIGGER_TYPES: dict[str, type] = {}


def _ensure_registry():
    """Lazy-load trigger types into registry."""
    if _TRIGGER_TYPES:
        return
    from kohakuterrarium.modules.trigger.timer import TimerTrigger
    from kohakuterrarium.modules.trigger.channel import ChannelTrigger
    from kohakuterrarium.modules.trigger.scheduler import SchedulerTrigger

    for cls in (TimerTrigger, ChannelTrigger, SchedulerTrigger):
        if getattr(cls, "universal", False):
            _TRIGGER_TYPES[cls.__name__] = cls


@register_builtin("create_trigger")
class CreateTriggerTool(BaseTool):
    """Create a trigger dynamically (timer, scheduler, channel watcher)."""

    needs_context = True
    require_manual_read = True  # Must read docs before using

    @property
    def tool_name(self) -> str:
        return "create_trigger"

    @property
    def description(self) -> str:
        return "Create a trigger (timer, scheduler, channel). Use info tool to read docs first."

    @property
    def execution_mode(self) -> ExecutionMode:
        return ExecutionMode.DIRECT

    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "trigger_type": {
                    "type": "string",
                    "description": "Trigger type: TimerTrigger, SchedulerTrigger, ChannelTrigger",
                },
                "trigger_id": {
                    "type": "string",
                    "description": "Unique ID for this trigger (optional)",
                },
                "config": {
                    "type": "object",
                    "description": "Trigger config (depends on type). See docs.",
                },
            },
            "required": ["trigger_type", "config"],
        }

    async def _execute(
        self, args: dict[str, Any], context: ToolContext | None = None
    ) -> ToolResult:
        if not context or not context.agent:
            return ToolResult(error="Agent context required", exit_code=1)

        trigger_type = args.get("trigger_type", "").strip()
        trigger_id = args.get("trigger_id", "").strip() or None
        config = args.get("config", {})

        if not trigger_type:
            return ToolResult(error="trigger_type is required", exit_code=1)

        _ensure_registry()
        cls = _TRIGGER_TYPES.get(trigger_type)
        if not cls:
            available = ", ".join(_TRIGGER_TYPES.keys())
            return ToolResult(
                error=f"Unknown trigger type: {trigger_type}. Available: {available}",
                exit_code=1,
            )

        try:
            trigger = cls.from_resume_dict(config)
        except Exception as e:
            return ToolResult(
                error=f"Failed to create {trigger_type}: {e}", exit_code=1
            )

        # Wire registry for ChannelTrigger
        if hasattr(trigger, "_registry") and trigger._registry is None:
            if context.agent.environment:
                trigger._registry = context.agent.environment.shared_channels
            elif context.session:
                trigger._registry = context.session.channels

        # Wire ignore_sender for channel triggers
        if hasattr(trigger, "ignore_sender") and not trigger.ignore_sender:
            trigger.ignore_sender = context.agent_name

        try:
            tid = await context.agent.trigger_manager.add(
                trigger, trigger_id=trigger_id
            )
            logger.info("Trigger created", trigger_id=tid, trigger_type=trigger_type)
            return ToolResult(
                output=f"Trigger created: {tid} ({trigger_type})",
                exit_code=0,
            )
        except Exception as e:
            return ToolResult(error=f"Failed to add trigger: {e}", exit_code=1)
