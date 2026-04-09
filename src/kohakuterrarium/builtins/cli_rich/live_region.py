"""Live region — state holder for the streaming chat region.

Holds:
  - Optional compaction banner (top)
  - The currently streaming assistant message
  - Active top-level tool blocks (sub-agents nest their children inline)
  - Background-promoted tasks (compact strip)

Renders to ANSI text via ``to_ansi(width)`` so the prompt_toolkit
``FormattedTextControl`` in the Application layout can display it.
"""

import time
from io import StringIO

from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from kohakuterrarium.builtins.cli_rich.blocks.footer import FooterBlock
from kohakuterrarium.builtins.cli_rich.blocks.message import AssistantMessageBlock
from kohakuterrarium.builtins.cli_rich.blocks.tool import ToolCallBlock
from kohakuterrarium.builtins.cli_rich.theme import (
    COLOR_AI,
    COLOR_COMPACT_BANNER,
    ICON_COMPACT,
    THINKING_LABEL,
    spinner_frame,
)


def render_to_ansi(renderable: RenderableType, width: int) -> str:
    """Render a Rich renderable to an ANSI-colored string."""
    buf = StringIO()
    console = Console(
        file=buf,
        force_terminal=True,
        color_system="truecolor",
        width=max(20, width),
        legacy_windows=False,
        soft_wrap=False,
        emoji=False,
    )
    console.print(renderable, end="")
    return buf.getvalue()


class LiveRegion:
    """Manages the live (re-rendered) region above the prompt."""

    def __init__(self):
        self.assistant_msg: AssistantMessageBlock | None = None
        # All tool blocks indexed by job_id (top-level + nested)
        self.tool_blocks: dict[str, ToolCallBlock] = {}
        # Top-level rendering order — backgrounded tools STAY here, they
        # just get a (bg) tag. This avoids the input box jumping around
        # when a job is promoted.
        self._top_order: list[str] = []
        self.footer = FooterBlock()
        self._compacting = False
        # Thinking indicator (LLM running but no tokens yet)
        self._thinking = False
        self._thinking_started_at: float = 0.0
        # Counter for synthetic sub-agent child block ids
        self._sa_child_counter = 0

    # ── Assistant message ──

    def start_message(self) -> None:
        if self.assistant_msg is None or self.assistant_msg._finished:
            self.assistant_msg = AssistantMessageBlock()
        # Show the thinking spinner until the first chunk arrives.
        self.set_thinking(True)

    def append_chunk(self, chunk: str) -> None:
        if self.assistant_msg is None:
            self.start_message()
        if self.assistant_msg is not None:
            self.assistant_msg.append(chunk)
        if chunk:
            # First chunk arrived → drop the spinner.
            self.set_thinking(False)

    def finish_message(self) -> RenderableType | None:
        """Finish the current assistant message and return its committed form."""
        self.set_thinking(False)
        if self.assistant_msg is None:
            return None
        if self.assistant_msg.is_empty:
            self.assistant_msg = None
            return None
        committed = self.assistant_msg.to_committed()
        self.assistant_msg.finish()
        self.assistant_msg = None
        return committed

    def set_thinking(self, value: bool) -> None:
        if value and not self._thinking:
            self._thinking_started_at = time.monotonic()
        self._thinking = value

    # ── Tool blocks ──

    def add_tool(
        self,
        job_id: str,
        name: str,
        args_preview: str = "",
        kind: str = "tool",
        parent_job_id: str = "",
    ) -> None:
        if not job_id:
            job_id = name  # Fallback if no job id

        # Idempotent: if a block with this job_id already exists, just
        # refresh its mutable fields (in case the second event has more
        # info than the first). Prevents duplicate panels when the same
        # sub-agent fires both subagent_start and tool_start, or when an
        # event is delivered twice.
        existing = self.tool_blocks.get(job_id)
        if existing is not None:
            if args_preview:
                existing.args_preview = args_preview
            if name and not existing.name:
                existing.name = name
            return

        block = ToolCallBlock(
            job_id=job_id,
            name=name,
            args_preview=args_preview,
            kind=kind,
            parent_job_id=parent_job_id,
        )
        self.tool_blocks[job_id] = block

        # If parent is known and active, nest under it; else top-level.
        parent = self.tool_blocks.get(parent_job_id) if parent_job_id else None
        if parent is not None:
            parent.add_child(block)
        else:
            self._top_order.append(job_id)

    def update_tool_done(
        self, job_id: str, output: str = "", **metadata
    ) -> RenderableType | None:
        block = self.tool_blocks.get(job_id)
        if block is None:
            return None
        block.set_done(output, **metadata)
        return self._finalize_block(block)

    def update_tool_error(self, job_id: str, error: str = "") -> RenderableType | None:
        block = self.tool_blocks.get(job_id)
        if block is None:
            return None
        block.set_error(error)
        return self._finalize_block(block)

    def _finalize_block(self, block: ToolCallBlock) -> RenderableType | None:
        """Remove the block from tracking and return its committed form.

        Children-of-something don't commit on their own — their parent
        commits the whole tree.
        """
        job_id = block.job_id

        # Nested child of an active parent: don't commit yet
        if block.parent_job_id and block.parent_job_id in self.tool_blocks:
            return None

        # Top-level: commit + remove (and drop any descendants from index)
        if job_id in self._top_order:
            self._top_order.remove(job_id)
        self._drop_subtree(block)
        return block.to_committed()

    def _drop_subtree(self, block: ToolCallBlock) -> None:
        """Remove block and all its descendants from tool_blocks."""
        for child in block.children:
            self._drop_subtree(child)
        self.tool_blocks.pop(block.job_id, None)

    # ── Sub-agent nested tools (subagent_tool_*) ──

    def add_subagent_tool(
        self, parent_id: str, tool_name: str, args_preview: str = ""
    ) -> str | None:
        """Add a child tool block under a sub-agent's parent block.

        Returns the synthetic child id, or None if the parent doesn't exist.
        """
        parent = self.tool_blocks.get(parent_id)
        if parent is None:
            return None
        self._sa_child_counter += 1
        child_id = f"{parent_id}::sub::{tool_name}::{self._sa_child_counter}"
        child = ToolCallBlock(
            job_id=child_id,
            name=tool_name,
            args_preview=args_preview,
            kind="tool",
            parent_job_id=parent_id,
        )
        self.tool_blocks[child_id] = child
        parent.add_child(child)
        return child_id

    def _find_open_subagent_tool(
        self, parent_id: str, tool_name: str
    ) -> ToolCallBlock | None:
        """Find the OLDEST still-running child of (parent_id, tool_name).

        Sub-agents complete tools in FIFO order (sequential LLM loop), so
        when ``tool_done`` for "bash" arrives we want to close the oldest
        unclosed bash, not the most recently-started one. The previous
        version used reversed() and would close the wrong block when the
        same tool name is called twice in quick succession.
        """
        parent = self.tool_blocks.get(parent_id)
        if parent is None:
            return None
        for child in parent.children:
            if child.name == tool_name and child.status == "running":
                return child
        return None

    def update_subagent_tool_done(
        self, parent_id: str, tool_name: str, output: str = ""
    ) -> None:
        block = self._find_open_subagent_tool(parent_id, tool_name)
        if block is None:
            return
        block.set_done(output)

    def update_subagent_tool_error(
        self, parent_id: str, tool_name: str, error: str = ""
    ) -> None:
        block = self._find_open_subagent_tool(parent_id, tool_name)
        if block is None:
            return
        block.set_error(error)

    def update_subagent_tokens(
        self, parent_id: str, prompt: int, completion: int, total: int
    ) -> None:
        parent = self.tool_blocks.get(parent_id)
        if parent is None:
            return
        parent.update_running_tokens(prompt, completion, total)

    def promote_tool(self, job_id: str) -> None:
        """Mark a tool as backgrounded. The block stays in the live region
        with a (bg) tag until it actually finishes — the user keeps full
        visibility of the running job."""
        block = self.tool_blocks.get(job_id)
        if block is None:
            return
        block.promote_to_background()

    def remove_tool(self, job_id: str) -> None:
        block = self.tool_blocks.pop(job_id, None)
        if block is None:
            return
        if job_id in self._top_order:
            self._top_order.remove(job_id)

    def cancel_tool(self, job_id: str) -> RenderableType | None:
        """Mark a tool as cancelled and finalize it."""
        block = self.tool_blocks.get(job_id)
        if block is None:
            return None
        block.set_error("cancelled")
        return self._finalize_block(block)

    def latest_running_direct_job_id(self) -> str | None:
        """Return the most recently started, still-running, non-background
        top-level job. Used by Ctrl+B backgroundify."""
        for job_id in reversed(self._top_order):
            block = self.tool_blocks.get(job_id)
            if block is None:
                continue
            if block.status == "running" and not block.is_background:
                return job_id
        return None

    def latest_running_bg_job_id(self) -> tuple[str, str] | None:
        """Return (job_id, name) for the most recent running, backgrounded
        top-level job. Used by Ctrl+X cancel."""
        for job_id in reversed(self._top_order):
            block = self.tool_blocks.get(job_id)
            if block is None:
                continue
            if block.status == "running" and block.is_background:
                return job_id, block.name
        return None

    # ── Footer pass-through ──

    def update_footer_tokens(
        self, prompt: int, completion: int, max_ctx: int = 0
    ) -> None:
        self.footer.update_tokens(prompt, completion, max_ctx)

    def update_footer_model(self, model: str) -> None:
        self.footer.update_model(model)

    def set_compacting(self, value: bool) -> None:
        self._compacting = value
        self.footer.set_compacting(value)

    def set_processing(self, value: bool) -> None:
        self.footer.set_processing(value)

    # ── Rendering ──

    def _render_compaction_banner(self) -> RenderableType:
        return Panel(
            Text(
                f"{ICON_COMPACT} Compacting conversation history…",
                style=COLOR_COMPACT_BANNER,
            ),
            border_style="yellow",
            padding=(0, 1),
            expand=True,
        )

    @property
    def has_content(self) -> bool:
        """True if the live region has anything to render (besides the footer)."""
        if self._compacting:
            return True
        if self._thinking:
            return True
        if self.assistant_msg is not None and not self.assistant_msg.is_empty:
            return True
        if self._top_order:
            return True
        return False

    def _render_thinking_line(self) -> RenderableType:
        now = time.monotonic()
        elapsed = now - self._thinking_started_at if self._thinking_started_at else 0.0
        frame = spinner_frame(now)
        line = Text()
        line.append(f"{frame} ", style="bold magenta")
        line.append(f"{THINKING_LABEL}…", style=COLOR_AI)
        if elapsed >= 1.0:
            line.append(f"  ({elapsed:.0f}s)", style="dim")
        return line

    def _build_renderable(self) -> RenderableType:
        """Build a Rich Group of just the live items (no footer)."""
        items: list[RenderableType] = []

        if self._compacting:
            items.append(self._render_compaction_banner())

        if self.assistant_msg is not None and not self.assistant_msg.is_empty:
            items.append(self.assistant_msg)
        elif self._thinking:
            items.append(self._render_thinking_line())

        for job_id in self._top_order:
            block = self.tool_blocks.get(job_id)
            if block is not None:
                items.append(block)

        if not items:
            return Text("")
        return Group(*items)

    def __rich__(self) -> RenderableType:
        return self._build_renderable()

    def to_ansi(self, width: int) -> str:
        """Render live items (no footer) to an ANSI-colored string."""
        if not self.has_content:
            return ""
        return render_to_ansi(self._build_renderable(), width).rstrip("\n")

    def footer_to_ansi(self, width: int) -> str:
        """Render the footer to an ANSI-colored string."""
        return render_to_ansi(self.footer, width).rstrip("\n")
