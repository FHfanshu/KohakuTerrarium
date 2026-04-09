"""Footer block — single-line status displayed at the bottom of the live region.

Shows token usage, model, mode hints, and compaction state.
"""

from rich.text import Text

from kohakuterrarium.builtins.cli_rich.theme import COLOR_FOOTER


def _fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


class FooterBlock:
    """One-line status footer at the bottom of the live region."""

    def __init__(self):
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._max_context = 0
        self._model = ""
        self._compacting = False
        self._processing = False

    def update_tokens(self, prompt: int, completion: int, max_ctx: int = 0) -> None:
        self._prompt_tokens = prompt
        self._completion_tokens = completion
        if max_ctx:
            self._max_context = max_ctx

    def update_model(self, model: str) -> None:
        self._model = model

    def set_compacting(self, value: bool) -> None:
        self._compacting = value

    def set_processing(self, value: bool) -> None:
        self._processing = value

    def __rich__(self) -> Text:
        parts: list[str] = []

        # Context window: percentage in front, raw counts after.
        if self._prompt_tokens or self._completion_tokens:
            if self._max_context > 0 and self._prompt_tokens > 0:
                pct = int(self._prompt_tokens / self._max_context * 100)
                parts.append(f"ctx {pct}%/{_fmt_tokens(self._max_context)}")
            tok = (
                f"{_fmt_tokens(self._prompt_tokens)}↑ "
                f"{_fmt_tokens(self._completion_tokens)}↓"
            )
            parts.append(tok)

        if self._model:
            parts.append(self._model)

        if self._compacting:
            parts.append("⟳ compacting")

        if self._processing:
            parts.append("esc=interrupt  ctrl+b=bg  ctrl+x=cancel-bg")
        else:
            parts.append("/help  /exit  shift+enter=newline  ctrl+d=quit")

        line = "  ·  ".join(parts) if parts else "ready"
        return Text(line, style=COLOR_FOOTER)
