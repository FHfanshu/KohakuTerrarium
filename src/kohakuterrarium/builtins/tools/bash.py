"""
Bash command execution tool.

Executes shell commands and returns output.
"""

import asyncio
import os
import shutil
import sys
from typing import Any

from kohakuterrarium.builtins.tools.registry import register_builtin
from kohakuterrarium.modules.tool.base import (
    BaseTool,
    ExecutionMode,
    ToolConfig,
    ToolResult,
)
from kohakuterrarium.utils.logging import get_logger

logger = get_logger(__name__)


@register_builtin("bash")
class BashTool(BaseTool):
    """
    Tool for executing bash/shell commands.

    On Windows, uses PowerShell Core (pwsh) or Windows PowerShell.
    On Unix, uses bash or sh.
    """

    def __init__(self, config: ToolConfig | None = None):
        super().__init__(config)
        self._shell = self._detect_shell()

    def _detect_shell(self) -> list[str]:
        """Detect the appropriate shell for the platform."""
        if sys.platform == "win32":
            # Prefer PowerShell Core (pwsh) over Windows PowerShell
            if shutil.which("pwsh"):
                return ["pwsh", "-NoProfile", "-NonInteractive", "-Command"]
            else:
                return [
                    "powershell",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                ]
        else:
            # Use bash on Unix, fallback to sh
            if shutil.which("bash"):
                return ["bash", "-c"]
            else:
                return ["sh", "-c"]

    @property
    def tool_name(self) -> str:
        return "bash"

    @property
    def description(self) -> str:
        return "Execute shell commands (prefer dedicated tools for file ops)"

    @property
    def execution_mode(self) -> ExecutionMode:
        return ExecutionMode.DIRECT

    async def _execute(self, args: dict[str, Any]) -> ToolResult:
        """Execute the command."""
        command = args.get("command", "")
        if not command:
            return ToolResult(error="No command provided")

        # Reject no-op waiting commands (hallucination pattern)
        stripped = command.strip().lower()
        if stripped.startswith("echo") and any(
            w in stripped
            for w in ("waiting", "wait for", "still running", "in progress")
        ):
            return ToolResult(
                error="Do not use bash to fake-wait for background tasks. "
                "Background results arrive automatically. "
                "Just stop your response — do not echo/sleep/poll."
            )
        if stripped.startswith("sleep"):
            return ToolResult(
                error="Do not sleep to wait for background tasks. "
                "Results arrive automatically when ready. "
                "Just stop your response."
            )

        logger.debug("Executing command", command=command[:100])

        # Build the full command
        full_command = self._shell + [command]

        # Set up environment
        env = os.environ.copy()
        if self.config.env:
            env.update(self.config.env)

        # Set working directory
        cwd = self.config.working_dir or os.getcwd()

        try:
            # Create subprocess
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=cwd,
                env=env,
            )

            # Wait for completion with timeout
            try:
                stdout, _ = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.timeout if self.config.timeout > 0 else None,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    error=f"Command timed out after {self.config.timeout}s",
                    exit_code=-1,
                )

            # Decode output
            output = stdout.decode("utf-8", errors="replace") if stdout else ""

            # Truncate if needed
            if self.config.max_output > 0 and len(output) > self.config.max_output:
                output = output[: self.config.max_output]
                output += f"\n... (truncated, {len(stdout) - self.config.max_output} bytes omitted)"

            exit_code = process.returncode or 0

            logger.debug(
                "Command completed",
                exit_code=exit_code,
                output_length=len(output),
            )

            return ToolResult(
                output=output,
                exit_code=exit_code,
                error=(
                    None if exit_code == 0 else f"Command exited with code {exit_code}"
                ),
            )

        except FileNotFoundError:
            return ToolResult(error=f"Shell not found: {self._shell[0]}")
        except PermissionError:
            return ToolResult(error="Permission denied")
        except Exception as e:
            logger.error("Command execution failed", error=str(e))
            return ToolResult(error=str(e))


@register_builtin("python")
class PythonTool(BaseTool):
    """
    Tool for executing Python code.

    Executes Python code in a subprocess.
    """

    @property
    def tool_name(self) -> str:
        return "python"

    @property
    def description(self) -> str:
        return "Execute Python code and return output"

    @property
    def execution_mode(self) -> ExecutionMode:
        return ExecutionMode.DIRECT

    async def _execute(self, args: dict[str, Any]) -> ToolResult:
        """Execute Python code."""
        code = args.get("code", "")
        if not code:
            return ToolResult(error="No code provided")

        logger.debug("Executing Python code", code_length=len(code))

        # Use current Python interpreter
        python_cmd = [sys.executable, "-c", code]

        try:
            process = await asyncio.create_subprocess_exec(
                *python_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.config.working_dir or os.getcwd(),
            )

            try:
                stdout, _ = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.timeout if self.config.timeout > 0 else None,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    error=f"Python execution timed out after {self.config.timeout}s",
                    exit_code=-1,
                )

            output = stdout.decode("utf-8", errors="replace") if stdout else ""
            exit_code = process.returncode or 0

            return ToolResult(
                output=output,
                exit_code=exit_code,
                error=(
                    None if exit_code == 0 else f"Python exited with code {exit_code}"
                ),
            )

        except Exception as e:
            logger.error("Python execution failed", error=str(e))
            return ToolResult(error=str(e))
