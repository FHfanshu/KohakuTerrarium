"""Audit plugin for the local SWE bio creature."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from kohakuterrarium.modules.plugin.base import BasePlugin, PluginContext
from kohakuterrarium.modules.tool.base import resolve_tool_path

DEFAULT_RULE_FILES = ["AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md", "README.md"]


def _discover_rule_paths(working_dir: Path, rule_files: list[str]) -> list[Path]:
    discovered: list[Path] = []
    seen: set[str] = set()
    current = working_dir.resolve()
    for directory in [current, *current.parents]:
        for filename in rule_files:
            candidate = directory / filename
            if not candidate.exists() or not candidate.is_file():
                continue
            normalized = str(candidate.resolve()).lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            discovered.append(candidate)
    return discovered


class AuditLoggerPlugin(BasePlugin):
    """Write a readable JSONL audit trail for work done by the creature."""

    name = "audit_logger"
    priority = 5

    def __init__(self, options: dict[str, Any] | None = None):
        opts = options or {}
        self._rule_files = list(opts.get("rule_files", DEFAULT_RULE_FILES))
        self._log_dir = Path(opts.get("log_dir", "./artifacts/audit"))
        self._redact_large_values = bool(opts.get("redact_large_values", True))
        self._task_preview_chars = int(opts.get("task_preview_chars", 240))
        self._output_preview_chars = int(opts.get("output_preview_chars", 240))
        self._working_dir = Path.cwd()
        self._session_id = ""
        self._agent_name = ""
        self._model = ""
        self._required_rules: list[Path] = []
        self._stream: Any = None

    async def on_load(self, context: PluginContext) -> None:
        self._working_dir = context.working_dir.resolve()
        self._session_id = context.session_id
        self._agent_name = context.agent_name
        self._model = context.model
        self._required_rules = _discover_rule_paths(self._working_dir, self._rule_files)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = self._log_dir / f"{self._agent_name}_{timestamp}.jsonl"
        self._stream = log_path.open("a", encoding="utf-8")
        self._emit(
            "agent_start",
            session_id=self._session_id,
            model=self._model,
            working_dir=str(self._working_dir),
            required_rules=[str(path) for path in self._required_rules],
        )

    async def on_unload(self) -> None:
        self._emit("plugin_unload")
        if self._stream:
            self._stream.close()
            self._stream = None

    async def on_agent_stop(self) -> None:
        self._emit("agent_stop")

    async def on_event(self, event: Any) -> None:
        event_type = getattr(event, "type", "")
        content = getattr(event, "content", "")
        payload = {"event_type": str(event_type)}
        if event_type == "user_input" and isinstance(content, str):
            payload["task_preview"] = self._clip(content, self._task_preview_chars)
        self._emit("event", **payload)

    async def pre_tool_execute(self, args: dict, **kwargs) -> dict | None:
        tool_name = str(kwargs.get("tool_name", ""))
        context = kwargs.get("context")
        payload = {
            "tool_name": tool_name,
            "job_id": kwargs.get("job_id", ""),
            "args": self._summarize_args(args),
        }
        candidate = self._resolve_arg_path(args, context)
        if tool_name == "read" and candidate and self._is_required_rule(candidate):
            payload["rule_file"] = str(candidate)
        self._emit("tool_start", **payload)
        return None

    async def post_tool_execute(self, result: Any, **kwargs) -> Any | None:
        tool_name = str(kwargs.get("tool_name", ""))
        args = kwargs.get("args", {}) or {}
        context = kwargs.get("context")
        error = getattr(result, "error", None)
        output = getattr(result, "output", "")
        payload = {
            "tool_name": tool_name,
            "job_id": kwargs.get("job_id", ""),
            "success": not bool(error),
            "error": str(error) if error else "",
            "output_preview": self._clip(str(output), self._output_preview_chars),
        }
        candidate = self._resolve_arg_path(args, context)
        if (
            tool_name == "read"
            and candidate
            and self._is_required_rule(candidate)
            and not error
        ):
            payload["rule_file"] = str(candidate)
            payload["rule_read"] = True
        self._emit("tool_end", **payload)
        return None

    async def pre_subagent_run(self, task: str, **kwargs) -> str | None:
        self._emit(
            "subagent_start",
            name=str(kwargs.get("name", "")),
            job_id=kwargs.get("job_id", ""),
            task_preview=self._clip(task, self._task_preview_chars),
            is_background=bool(kwargs.get("is_background", False)),
        )
        return None

    async def post_subagent_run(self, result: Any, **kwargs) -> Any | None:
        success = getattr(result, "success", None)
        error = getattr(result, "error", None)
        output = getattr(result, "output", "")
        self._emit(
            "subagent_end",
            name=str(kwargs.get("name", "")),
            job_id=kwargs.get("job_id", ""),
            success=success,
            error=str(error) if error else "",
            output_preview=self._clip(str(output), self._output_preview_chars),
        )
        return None

    def _emit(self, event: str, **payload: Any) -> None:
        if self._stream is None:
            return
        record = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "event": event,
            "agent_name": self._agent_name,
            "session_id": self._session_id,
            "working_dir": str(self._working_dir),
        }
        record.update(payload)
        self._stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._stream.flush()

    def _summarize_args(self, args: dict[str, Any]) -> dict[str, Any]:
        summary: dict[str, Any] = {}
        for key, value in args.items():
            if isinstance(value, str):
                if self._redact_large_values and key in {
                    "content",
                    "diff",
                    "new",
                    "old",
                }:
                    summary[key] = f"<{key}:{len(value)} chars>"
                else:
                    summary[key] = self._clip(value, self._task_preview_chars)
            elif isinstance(value, list):
                summary[key] = f"<list:{len(value)} items>"
            elif isinstance(value, dict):
                summary[key] = f"<dict:{len(value)} keys>"
            else:
                summary[key] = value
        return summary

    def _resolve_arg_path(self, args: dict[str, Any], context: Any) -> Path | None:
        path = args.get("path")
        if not isinstance(path, str) or not path or context is None:
            return None
        try:
            return resolve_tool_path(path, context)
        except Exception:
            working_dir = getattr(context, "working_dir", None)
            if working_dir is None:
                return None
            return (Path(working_dir) / path).resolve()

    def _is_required_rule(self, path: Path) -> bool:
        normalized = str(path.resolve()).lower()
        required = {
            str(candidate.resolve()).lower() for candidate in self._required_rules
        }
        return normalized in required

    def _clip(self, value: str, limit: int) -> str:
        if len(value) <= limit:
            return value
        return value[:limit] + "..."
