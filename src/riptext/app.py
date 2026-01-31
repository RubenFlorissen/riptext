"""Riptext TUI application."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

from textual.app import App, ComposeResult, SystemCommand
from textual.binding import Binding
from textual.widgets import Input, Label, TextArea

from .commands import RipCommandProvider
from .core.execution import run_script
from .core.models import ScriptMetadata
from .core.scripts import ScriptIndex, load_all_scripts
from .save import handle_save_submit, toggle_save_input
from .selection import (
    MODE_LABELS,
    SelectionMode,
    cycle_mode,
    get_selections,
)
from .syntax import detect_language


class RiptextApp(App):
    """Main riptext application."""

    CSS = """
    Screen { layout: vertical; }
    #editor { height: 1fr; }
    #status { height: 1; }
    #save-input { display: none; height: auto; margin: 0; padding: 0; }
    #save-input.visible { display: block; }
    """

    COMMANDS = App.COMMANDS | {RipCommandProvider}
    COMMAND_PALETTE_BINDING = "ctrl+b"

    BINDINGS = [
        ("ctrl+r", "run_last", "Run last"),
        ("ctrl+l", "cycle_mode", "Cycle selection mode"),
        ("ctrl+s", "save", "Save file"),
        Binding("ctrl+z", "undo_transform", "Undo last transform", priority=True),
        Binding("ctrl+x", "quit", "Quit", priority=True),
        Binding("ctrl+q", "noop", show=False),
    ]

    def __init__(
        self,
        user_scripts_dir: Path | None = None,
        initial_text: str | None = None,
        file_path: Path | None = None,
        cwd: Path | None = None,
    ) -> None:
        super().__init__()
        self._user_scripts_dir = user_scripts_dir
        self._initial_text = initial_text
        self._file_path = file_path
        self._cwd = cwd or Path.cwd()
        self._index: ScriptIndex | None = None
        self._last_script: ScriptMetadata | None = None
        self._pre_transform_text: str | None = None
        self._debug_keys = os.environ.get("RIPTEXT_DEBUG_KEYS") == "1"
        self._selection_mode: SelectionMode = "full"

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield TextArea(id="editor")
        default_path = str(self._file_path or self._cwd / "untitled.txt")
        yield Input(value=default_path, placeholder="File path to save...", id="save-input")
        yield Label("", id="status")

    def on_mount(self) -> None:
        self._reload_scripts()
        editor = self.query_one("#editor", TextArea)
        if self._initial_text:
            editor.text = self._initial_text
        self._apply_syntax_highlighting(editor)
        editor.focus()
        if os.environ.get("TERM_PROGRAM") == "vscode" or os.environ.get("VSCODE_PID"):
            self._set_status(
                "VS Code terminal may not capture TUI keys. Use an external terminal.",
                error=True,
            )
        else:
            self._show_mode()

    # -------------------------------------------------------------------------
    # Event handlers
    # -------------------------------------------------------------------------

    def on_key(self, event) -> None:  # type: ignore[override]
        if self._debug_keys:
            self._set_status(f"Key: {event.key} {event.character or ''}".strip())

        # Handle Escape in save input
        save_input = self.query_one("#save-input", Input)
        if save_input.has_class("visible") and event.key == "escape":
            save_input.remove_class("visible")
            self.query_one("#editor", TextArea).focus()
            self._show_mode()
            event.prevent_default()
            event.stop()

    def on_text_area_selection_changed(self, event: TextArea.SelectionChanged) -> None:
        """Auto-switch to selection mode when text is selected."""
        sel = event.selection
        has_selection = sel.start != sel.end
        if has_selection and self._selection_mode != "selection":
            self._selection_mode = "selection"
            self._show_mode()
        elif not has_selection and self._selection_mode == "selection":
            self._selection_mode = "full"
            self._show_mode()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle save input submission."""
        if event.input.id == "save-input":
            editor = self.query_one("#editor", TextArea)
            new_path = handle_save_submit(
                event.value, self._cwd, editor, self._set_status
            )
            if new_path:
                self._file_path = new_path
            event.input.remove_class("visible")
            editor.focus()

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------

    def action_noop(self) -> None:
        pass

    def action_quit(self) -> None:
        self.exit()

    def action_run_last(self) -> None:
        if self._last_script is None:
            self._set_status("No script run yet.", error=True)
            return
        self.run_script(self._last_script)

    def action_cycle_mode(self) -> None:
        self._selection_mode = cycle_mode(self._selection_mode)
        self._show_mode()

    def action_undo_transform(self) -> None:
        """Revert to text before last transform."""
        if self._pre_transform_text is None:
            self._set_status("Nothing to undo.", error=True)
            return
        editor = self.query_one("#editor", TextArea)
        current_text = editor.text
        editor.text = self._pre_transform_text
        self._pre_transform_text = current_text
        self._set_status("Undid last transform. (Ctrl+Z again to redo)", auto_clear=True)

    def action_save(self) -> None:
        """Toggle save input visibility."""
        toggle_save_input(
            self.query_one("#save-input", Input),
            self.query_one("#editor", TextArea),
            self._file_path,
            self._cwd,
            self._show_mode,
            self._set_status,
        )

    # -------------------------------------------------------------------------
    # Scripts
    # -------------------------------------------------------------------------

    def _reload_scripts(self) -> None:
        scripts = load_all_scripts(self._user_scripts_dir)
        self._index = ScriptIndex(scripts)

    def reload_scripts(self) -> None:
        """Public method for hot-reloading scripts."""
        self._reload_scripts()

    def scripts_for_commands(self) -> list[ScriptMetadata]:
        if not self._index:
            return []
        return sorted(self._index.scripts, key=lambda s: s.name.lower())

    def run_script(self, script: ScriptMetadata) -> None:
        editor = self.query_one("#editor", TextArea)

        # Handle special detect_language script
        if script.slug == "detect_language":
            self._run_detect_language(editor)
            return

        text = editor.text
        self._pre_transform_text = text
        selections = get_selections(editor, self._selection_mode)
        new_text, info, errors = run_script(script, text, selections)
        editor.text = new_text
        self._last_script = script

        if errors:
            self._set_status(errors[-1], error=True, auto_clear=True)
        elif info:
            self._set_status(info[-1], auto_clear=True)
        else:
            self._set_status(f"Ran {script.name}.", auto_clear=True)

    def _run_detect_language(self, editor: TextArea) -> None:
        """Handle the detect_language special script."""
        lang = detect_language(self._file_path, editor.text)
        if lang:
            editor.language = lang
            self._set_status(f"Detected: {lang}", auto_clear=True)
        else:
            self._set_status("Could not detect language", error=True, auto_clear=True)

    # -------------------------------------------------------------------------
    # Syntax highlighting
    # -------------------------------------------------------------------------

    def _apply_syntax_highlighting(self, editor: TextArea) -> None:
        """Detect and apply syntax highlighting."""
        lang = detect_language(self._file_path, editor.text)
        editor.language = lang

    # -------------------------------------------------------------------------
    # Status bar
    # -------------------------------------------------------------------------

    def _set_status(
        self, message: str, *, error: bool = False, auto_clear: bool = False
    ) -> None:
        label = self.query_one("#status", Label)
        label.update(message)
        label.styles.color = "red" if error else "white"
        if auto_clear:
            self.set_timer(2.0, self._show_mode)

    def _show_mode(self) -> None:
        self._set_status(f"Mode: {MODE_LABELS[self._selection_mode]} (Ctrl+L to change)")

    # -------------------------------------------------------------------------
    # System commands
    # -------------------------------------------------------------------------

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


def run_app(
    user_scripts_dir: Path | None = None,
    initial_text: str | None = None,
    file_path: Path | None = None,
    cwd: Path | None = None,
) -> None:
    """Entry point to run the application."""
    RiptextApp(
        user_scripts_dir,
        initial_text=initial_text,
        file_path=file_path,
        cwd=cwd,
    ).run()
