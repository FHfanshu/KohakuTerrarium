"""Guard plugin for the local SWE bio creature."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kohakuterrarium.modules.plugin.base import (
    BasePlugin,
    PluginBlockError,
    PluginContext,
)
from kohakuterrarium.modules.tool.base import resolve_tool_path
from kohakuterrarium.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_RULE_FILES = ["AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md", "README.md"]
DEFAULT_MUTATING_BASH_PATTERNS = [
    "rm ",
    "rm-",
    "rm\t",
    "del ",
    "erase ",
    "remove-item ",
    "set-content ",
    "add-content ",
    "out-file ",
    "copy-item ",
    "move-item ",
    "rename-item ",
    "new-item ",
    "git apply",
    "git am",
    "git cherry-pick",
    "git clean",
    "git commit",
    "git merge",
    "git push",
    "git rebase",
    "git reset",
    "git revert",
    "git switch",
    "git tag",
    "git checkout --",
    "sed -i",
]
DEFAULT_DANGEROUS_BASH_PATTERNS = [
    "rm -rf",
    "rm /s /q",
    "del /f /s /q",
    "remove-item -recurse -force",
    "git clean -fd",
    "git clean -fdx",
    "git reset --hard",
    "format ",
    "mkfs",
]


def _normalize_path(path: Path) -> str:
    return str(path.resolve()).lower()


def _discover_rule_paths(working_dir: Path, rule_files: list[str]) -> list[Path]:
    discovered: list[Path] = []
    seen: set[str] = set()

    current = working_dir.resolve()
    parents = [current, *current.parents]
    for directory in parents:
        for filename in rule_files:
            candidate = directory / filename
            if not candidate.exists() or not candidate.is_file():
                continue
            normalized = _normalize_path(candidate)
            if normalized in seen:
                continue
            seen.add(normalized)
            discovered.append(candidate)
    return discovered


class RulesGuardPlugin(BasePlugin):
    """Enforce repo-rule reading before mutation and block dangerous shell usage."""

    name = "rules_guard"
    priority = 1

    def __init__(self, options: dict[str, Any] | None = None):
        opts = options or {}
        self._rule_files = list(opts.get("rule_files", DEFAULT_RULE_FILES))
        self._modify_tools = set(
            opts.get("modify_tools", ["write", "edit", "multi_edit"])
        )
        self._guarded_subagents = set(opts.get("guarded_subagents", ["worker"]))
        self._block_mutating_bash_before_rules = bool(
            opts.get("block_mutating_bash_before_rules", True)
        )
        self._dangerous_bash_patterns = [
            pattern.lower()
            for pattern in opts.get(
                "dangerous_bash_patterns", DEFAULT_DANGEROUS_BASH_PATTERNS
            )
        ]
        self._mutating_bash_patterns = [
            pattern.lower()
            for pattern in opts.get(
                "mutating_bash_patterns", DEFAULT_MUTATING_BASH_PATTERNS
            )
        ]
        self._working_dir = Path.cwd()
        self._required_rules: list[Path] = []
        self._read_rules: set[str] = set()

    async def on_load(self, context: PluginContext) -> None:
        self._working_dir = context.working_dir.resolve()
        self._required_rules = _discover_rule_paths(self._working_dir, self._rule_files)
        self._read_rules = set(context.get_state("read_rule_files") or [])
        context.set_state(
            "required_rule_files", [str(path) for path in self._required_rules]
        )
        context.set_state("read_rule_files", sorted(self._read_rules))
        logger.info(
            "Rules guard loaded",
            working_dir=str(self._working_dir),
            required_rules=len(self._required_rules),
        )

    async def pre_tool_execute(self, args: dict, **kwargs) -> dict | None:
        tool_name = str(kwargs.get("tool_name", ""))
        context = kwargs.get("context")

        if tool_name == "bash":
            self._check_bash_command(str(args.get("command", "")))
            if self._block_mutating_bash_before_rules and self._has_unread_rules():
                if self._looks_mutating_bash(str(args.get("command", ""))):
                    raise PluginBlockError(self._missing_rules_message("bash mutation"))

        if tool_name in self._modify_tools and self._has_unread_rules():
            raise PluginBlockError(self._missing_rules_message(tool_name))

        if tool_name == "read" and context is not None:
            candidate = self._resolve_arg_path(args, context)
            if candidate and self._is_required_rule(candidate):
                logger.info("Rule file read requested", path=str(candidate))

        return None

    async def post_tool_execute(self, result: Any, **kwargs) -> Any | None:
        tool_name = str(kwargs.get("tool_name", ""))
        args = kwargs.get("args", {}) or {}
        context = kwargs.get("context")
        error = getattr(result, "error", None)

        if tool_name == "read" and not error and context is not None:
            candidate = self._resolve_arg_path(args, context)
            if candidate and self._is_required_rule(candidate):
                normalized = _normalize_path(candidate)
                self._read_rules.add(normalized)
                agent = getattr(context, "agent", None)
                session_store = getattr(agent, "session_store", None)
                if session_store is not None:
                    session_store.state[
                        f"plugin:{self.name}:read_rule_files"
                    ] = sorted(self._read_rules)
                logger.info("Rule file read completed", path=str(candidate))
        return None

    async def pre_subagent_run(self, task: str, **kwargs) -> str | None:
        name = str(kwargs.get("name", ""))
        if name in self._guarded_subagents and self._has_unread_rules():
            raise PluginBlockError(self._missing_rules_message(f"subagent:{name}"))
        return None

    def _resolve_arg_path(self, args: dict[str, Any], context: Any) -> Path | None:
        path = args.get("path")
        if not isinstance(path, str) or not path:
            return None
        try:
            return resolve_tool_path(path, context)
        except Exception:
            working_dir = getattr(context, "working_dir", None)
            if working_dir is None:
                return None
            return (Path(working_dir) / path).resolve()

    def _is_required_rule(self, path: Path) -> bool:
        normalized = _normalize_path(path)
        return normalized in {
            _normalize_path(candidate) for candidate in self._required_rules
        }

    def _has_unread_rules(self) -> bool:
        if not self._required_rules:
            return False
        required = {_normalize_path(path) for path in self._required_rules}
        return not required.issubset(self._read_rules)

    def _missing_rule_paths(self) -> list[str]:
        required = {_normalize_path(path): str(path) for path in self._required_rules}
        return [path for key, path in required.items() if key not in self._read_rules]

    def _missing_rules_message(self, action: str) -> str:
        missing = self._missing_rule_paths()
        missing_text = ", ".join(missing) if missing else "no missing rule files"
        return (
            f"Blocked {action}: read the discovered repository rule files first. "
            f"Missing: {missing_text}. "
            "If files conflict, follow the more specific file and the one closer to the current directory."
        )

    def _check_bash_command(self, command: str) -> None:
        normalized = command.casefold()
        for pattern in self._dangerous_bash_patterns:
            if pattern in normalized:
                raise PluginBlockError(
                    f"Blocked bash command: dangerous pattern detected ({pattern})."
                )

    def _looks_mutating_bash(self, command: str) -> bool:
        normalized = command.casefold()
        if ">" in normalized or ">>" in normalized:
            return True
        for pattern in self._mutating_bash_patterns:
            if pattern in normalized:
                return True
        return False
