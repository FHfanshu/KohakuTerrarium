"""Theme constants for the rich CLI — colors, glyphs, status icons."""

# Status glyphs
ICON_RUNNING = "●"
ICON_DONE = "✓"
ICON_ERROR = "✗"
ICON_USER = "▶"
ICON_AI = "◆"
ICON_THINKING = "…"
ICON_SUBAGENT = "↳"
ICON_BG = "⏳"
ICON_COMPACT = "⟳"

# Spinner frames (used by live blocks)
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# Thinking indicator label (Kohaku + UwU + ing)
THINKING_LABEL = "KohakUwUing"


def spinner_frame(now: float, fps: float = 5.0) -> str:
    """Return the spinner frame for the given monotonic time."""
    idx = int(now * fps) % len(SPINNER_FRAMES)
    return SPINNER_FRAMES[idx]


# Colors (Rich-compatible)
COLOR_RUNNING = "yellow"
COLOR_DONE = "green"
COLOR_ERROR = "red"
COLOR_USER = "cyan"
COLOR_AI = "magenta"
COLOR_DIM = "bright_black"
COLOR_FOOTER = "dim"
COLOR_TOOL_BORDER = "dim cyan"
COLOR_SUBAGENT_BORDER = "dim magenta"
COLOR_BG = "bright_blue"
COLOR_BANNER = "bold magenta"
COLOR_COMPACT_BANNER = "bold yellow on grey15"
