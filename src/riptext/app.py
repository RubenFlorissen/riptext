from __future__ import annotations

from functools import partial
from pathlib import Path
import os
from typing import Iterable, Literal

SelectionMode = Literal["full", "lines", "selection"]

from textual.app import App, ComposeResult, SystemCommand
from textual.command import DiscoveryHit, Hit, Hits, Provider
from textual.binding import Binding
from textual.widgets import Label, TextArea

from .core.execution import run_script
from .core.models import ScriptMetadata, SelectionRange
from .core.scripts import ScriptIndex, load_all_scripts


class RipCommandProvider(Provider):
    """Provide rip scripts to the command palette."""

    async def discover(self) -> Hits:
        app = self.app
        assert isinstance(app, RiptextApp)
        for script in app._scripts_for_commands()[:8]:
            yield DiscoveryHit(
                display=script.name,
                command=partial(app._run_script, script),
                help=script.description or None,
            )

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)
        app = self.app
        assert isinstance(app, RiptextApp)

        for script in app._scripts_for_commands():
            candidate = " ".join(
                [script.name, script.slug, script.description, " ".join(script.tags)]
            ).strip()
            score = matcher.match(candidate)
            if score <= 0:
                continue
            yield Hit(
                score,
                matcher.highlight(script.name),
                partial(app._run_script, script),
                help=script.description or None,
            )


class RiptextApp(App):
    CSS = """
    Screen { layout: vertical; }
    #editor { height: 1fr; }
    #status { color: $text-muted; height: 1; }
    """

    COMMANDS = App.COMMANDS | {RipCommandProvider}
    COMMAND_PALETTE_BINDING = "ctrl+b"

    BINDINGS = [
        ("ctrl+r", "run_last", "Run last"),
        ("ctrl+l", "cycle_mode", "Cycle selection mode"),
        Binding("ctrl+x", "quit", "Quit", priority=True),
        Binding("ctrl+q", "noop", show=False),  # unbind default quit
    ]

    def action_noop(self) -> None:
        pass

    def action_quit(self) -> None:
        self.exit()

    def __init__(self, user_scripts_dir: Path | None = None) -> None:
        super().__init__()
        self._user_scripts_dir = user_scripts_dir
        self._index: ScriptIndex | None = None
        self._last_script: ScriptMetadata | None = None
        self._debug_keys = os.environ.get("RIPTEXT_DEBUG_KEYS") == "1"
        self._selection_mode: SelectionMode = "full"

    def compose(self) -> ComposeResult:
        yield TextArea(id="editor")
        yield Label("", id="status")

    def on_mount(self) -> None:
        self._reload_scripts()
        self.query_one("#editor", TextArea).focus()
        if os.environ.get("TERM_PROGRAM") == "vscode" or os.environ.get("VSCODE_PID"):
            self._set_status(
                "VS Code terminal may not capture TUI keys. Use an external terminal.",
                error=True,
            )
        else:
            self._show_mode()

    def on_key(self, event) -> None:  # type: ignore[override]
        if self._debug_keys:
            key_name = event.key
            char = event.character or ""
            self._set_status(f"Key: {key_name} {char}".strip())

    def _reload_scripts(self) -> None:
        scripts = load_all_scripts(self._user_scripts_dir)
        self._index = ScriptIndex(scripts)

    def _set_status(self, message: str, *, error: bool = False, auto_clear: bool = False) -> None:
        label = self.query_one("#status", Label)
        label.update(message)
        label.styles.color = "red" if error else "green"
        if auto_clear:
            self.set_timer(2.0, self._show_mode)

    def action_run_last(self) -> None:
        if self._last_script is None:
            self._set_status("No script run yet.", error=True)
            return
        self._run_script(self._last_script)

    def action_cycle_mode(self) -> None:
        modes: list[SelectionMode] = ["full", "lines", "selection"]
        idx = modes.index(self._selection_mode)
        self._selection_mode = modes[(idx + 1) % len(modes)]
        self._show_mode()

    def _show_mode(self) -> None:
        labels = {"full": "Full text", "lines": "Current line", "selection": "Selection"}
        self._set_status(f"Mode: {labels[self._selection_mode]} (Ctrl+L to change)")

    def _get_selections(self) -> list[SelectionRange]:
        editor = self.query_one("#editor", TextArea)
        text = editor.text

        if self._selection_mode == "full":
            return []

        if self._selection_mode == "lines":
            # Current line mode: get the line where cursor is
            cursor = editor.cursor_location
            row = cursor[0]
            lines = text.split("\n")
            # Calculate start offset for the current line
            start = sum(len(lines[i]) + 1 for i in range(row))
            end = start + len(lines[row]) if row < len(lines) else start
            return [SelectionRange(start, end)]

        # selection mode: use TextArea's selection
        sel = editor.selection
        start_loc = sel.start
        end_loc = sel.end
        # Convert (row, col) to character offset
        lines = text.split("\n")
        def loc_to_offset(row: int, col: int) -> int:
            offset = sum(len(lines[i]) + 1 for i in range(row))
            return offset + col
        start_offset = loc_to_offset(start_loc[0], start_loc[1])
        end_offset = loc_to_offset(end_loc[0], end_loc[1])
        if start_offset == end_offset:
            return []  # no selection, fall back to full text
        return [SelectionRange(min(start_offset, end_offset), max(start_offset, end_offset))]

    def _scripts_for_commands(self) -> list[ScriptMetadata]:
        if not self._index:
            return []
        return sorted(self._index.scripts, key=lambda script: script.name.lower())

    def _run_script(self, script: ScriptMetadata) -> None:
        editor = self.query_one("#editor", TextArea)
        text = editor.text
        selections = self._get_selections()
        new_text, info, errors = run_script(script, text, selections)
        editor.text = new_text
        self._last_script = script
        if errors:
            self._set_status(errors[-1], error=True, auto_clear=True)
        elif info:
            self._set_status(info[-1], auto_clear=True)
        else:
            self._set_status(f"Ran {script.name}.", auto_clear=True)

    def get_system_commands(self, screen) -> Iterable[SystemCommand]:
        for command in super().get_system_commands(screen):
            yield SystemCommand(
                f"Settings: {command.title}",
                command.help,
                command.callback,
                discover=False,
            )
        yield SystemCommand(
            "Settings: Run last rip",
            "Re-run the most recently executed script (Ctrl+R)",
            self.action_run_last,
            discover=False,
        )


def run_app(user_scripts_dir: Path | None = None) -> None:
    RiptextApp(user_scripts_dir).run()
