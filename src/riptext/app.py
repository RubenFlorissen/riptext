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
from .favorites import add_recent, toggle_favorite
from .macros import save_macro
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
    #find-input { display: none; height: auto; margin: 0; padding: 0; }
    #find-input.visible { display: block; }
    #goto-input { display: none; height: auto; margin: 0; padding: 0; }
    #goto-input.visible { display: block; }
    #macro-input { display: none; height: auto; margin: 0; padding: 0; }
    #macro-input.visible { display: block; }
    """

    COMMANDS = App.COMMANDS | {RipCommandProvider}
    COMMAND_PALETTE_BINDING = "ctrl+b"

    BINDINGS = [
        ("ctrl+r", "run_last", "Run last"),
        ("ctrl+l", "cycle_mode", "Cycle selection mode"),
        ("ctrl+s", "save", "Save file"),
        Binding("ctrl+f", "find", "Find", priority=True),
        Binding("ctrl+g", "goto_line", "Go to line", priority=True),
        Binding("ctrl+n", "toggle_line_numbers", "Toggle line numbers", priority=True),
        Binding("ctrl+w", "toggle_word_wrap", "Toggle word wrap", priority=True),
        Binding("ctrl+z", "undo_transform", "Undo last transform", priority=True),
        Binding("ctrl+d", "toggle_favorite", "Toggle favorite", priority=True),
        Binding("ctrl+m", "start_macro", "Record/save macro", priority=True),
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
        self._macro_recording: list[str] = []
        self._is_recording_macro = False

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield TextArea(id="editor", show_line_numbers=True)
        default_path = str(self._file_path or self._cwd / "untitled.txt")
        yield Input(value=default_path, placeholder="File path to save...", id="save-input")
        yield Input(placeholder="Find text...", id="find-input")
        yield Input(placeholder="Go to line number...", id="goto-input")
        yield Input(placeholder="Macro name (Enter to save)...", id="macro-input")
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

        # Handle Escape in overlay inputs
        for input_id in ["#save-input", "#find-input", "#goto-input", "#macro-input"]:
            inp = self.query_one(input_id, Input)
            if inp.has_class("visible") and event.key == "escape":
                inp.remove_class("visible")
                self.query_one("#editor", TextArea).focus()
                self._show_mode()
                event.prevent_default()
                event.stop()
                return

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
        """Handle input submissions."""
        editor = self.query_one("#editor", TextArea)
        
        if event.input.id == "save-input":
            new_path = handle_save_submit(
                event.value, self._cwd, editor, self._set_status
            )
            if new_path:
                self._file_path = new_path
        
        elif event.input.id == "find-input":
            self._do_find(event.value, editor)
        
        elif event.input.id == "goto-input":
            self._do_goto_line(event.value, editor)

        elif event.input.id == "macro-input":
            self._save_macro(event.value)

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

    def action_find(self) -> None:
        """Show find input."""
        self._hide_all_inputs()
        find_input = self.query_one("#find-input", Input)
        find_input.value = ""
        find_input.add_class("visible")
        find_input.focus()
        self._set_status("Enter text to find, press Enter to search (F3/Ctrl+F to find next)")

    def action_goto_line(self) -> None:
        """Show go to line input."""
        self._hide_all_inputs()
        goto_input = self.query_one("#goto-input", Input)
        goto_input.value = ""
        goto_input.add_class("visible")
        goto_input.focus()
        self._set_status("Enter line number and press Enter")

    def action_toggle_line_numbers(self) -> None:
        """Toggle line numbers display."""
        editor = self.query_one("#editor", TextArea)
        editor.show_line_numbers = not editor.show_line_numbers
        state = "on" if editor.show_line_numbers else "off"
        self._set_status(f"Line numbers {state}", auto_clear=True)

    def action_toggle_word_wrap(self) -> None:
        """Toggle word wrap."""
        editor = self.query_one("#editor", TextArea)
        editor.soft_wrap = not editor.soft_wrap
        state = "on" if editor.soft_wrap else "off"
        self._set_status(f"Word wrap {state}", auto_clear=True)

    def _hide_all_inputs(self) -> None:
        """Hide all overlay inputs."""
        for input_id in ["#save-input", "#find-input", "#goto-input", "#macro-input"]:
            self.query_one(input_id, Input).remove_class("visible")

    def _do_find(self, query: str, editor: TextArea) -> None:
        """Find text in editor."""
        if not query:
            return
        text = editor.text
        cursor_pos = editor.cursor_location
        # Convert cursor to offset
        lines = text.split("\n")
        offset = sum(len(lines[i]) + 1 for i in range(cursor_pos[0])) + cursor_pos[1]
        # Search from cursor
        pos = text.find(query, offset + 1)
        if pos == -1:
            pos = text.find(query)  # Wrap around
        if pos == -1:
            self._set_status(f"'{query}' not found", error=True, auto_clear=True)
            return
        # Convert offset to row, col
        row, col = 0, 0
        for i, line in enumerate(lines):
            if pos <= len(line):
                row, col = i, pos
                break
            pos -= len(line) + 1
        editor.cursor_location = (row, col)
        editor.selection = ((row, col), (row, col + len(query)))
        self._set_status(f"Found '{query}'", auto_clear=True)
        self._last_find_query = query

    def _do_goto_line(self, line_str: str, editor: TextArea) -> None:
        """Go to specified line number."""
        try:
            line_num = int(line_str)
        except ValueError:
            self._set_status("Invalid line number", error=True, auto_clear=True)
            return
        lines = editor.text.split("\n")
        if line_num < 1 or line_num > len(lines):
            self._set_status(f"Line {line_num} out of range (1-{len(lines)})", error=True, auto_clear=True)
            return
        editor.cursor_location = (line_num - 1, 0)
        self._set_status(f"Jumped to line {line_num}", auto_clear=True)

    def action_toggle_favorite(self) -> None:
        """Toggle the last-run script as favorite."""
        if self._last_script is None:
            self._set_status("Run a script first to favorite it.", error=True, auto_clear=True)
            return
        is_fav = toggle_favorite(self._last_script.slug)
        star = "★ Favorited" if is_fav else "☆ Unfavorited"
        self._set_status(f"{star}: {self._last_script.name}", auto_clear=True)

    def action_start_macro(self) -> None:
        """Toggle macro recording or save a recorded macro."""
        if not self._is_recording_macro:
            self._is_recording_macro = True
            self._macro_recording = []
            self._set_status("🔴 Recording macro… Run scripts, then Ctrl+M to save.")
        else:
            if not self._macro_recording:
                self._is_recording_macro = False
                self._set_status("Macro cancelled (no scripts recorded).", auto_clear=True)
                return
            # Show input to name the macro
            self._hide_all_inputs()
            macro_input = self.query_one("#macro-input", Input)
            macro_input.value = ""
            macro_input.add_class("visible")
            macro_input.focus()
            self._set_status(
                f"Name this macro ({len(self._macro_recording)} scripts recorded):"
            )

    def _save_macro(self, name: str) -> None:
        """Save the recorded macro."""
        self._is_recording_macro = False
        if not name.strip():
            self._set_status("Macro cancelled.", auto_clear=True)
            return
        path = save_macro(name.strip(), self._macro_recording)
        self._set_status(
            f"Saved macro '{name}' ({len(self._macro_recording)} scripts) → {path}",
            auto_clear=True,
        )
        self._macro_recording = []

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

        # Track usage
        add_recent(script.slug)
        if self._is_recording_macro:
            self._macro_recording.append(script.slug)

        if errors:
            self._set_status(errors[-1], error=True, auto_clear=True)
        elif info:
            self._set_status(info[-1], auto_clear=True)
        else:
            rec = " 🔴" if self._is_recording_macro else ""
            self._set_status(f"Ran {script.name}.{rec}", auto_clear=True)

    def run_macro(self, slugs: list[str]) -> None:
        """Run a sequence of scripts (macro)."""
        editor = self.query_one("#editor", TextArea)
        text = editor.text
        self._pre_transform_text = text

        all_errors: list[str] = []
        ran = 0
        for slug in slugs:
            script = self._find_script_by_slug(slug)
            if not script:
                all_errors.append(f"Script '{slug}' not found")
                continue
            selections = get_selections(editor, self._selection_mode)
            new_text, _, errors = run_script(script, editor.text, selections)
            editor.text = new_text
            all_errors.extend(errors)
            ran += 1

        if all_errors:
            self._set_status(all_errors[-1], error=True, auto_clear=True)
        else:
            self._set_status(f"Macro complete ({ran} scripts).", auto_clear=True)

    def _find_script_by_slug(self, slug: str) -> ScriptMetadata | None:
        """Find a script by slug."""
        if not self._index:
            return None
        for s in self._index.scripts:
            if s.slug == slug:
                return s
        return None

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
        yield SystemCommand(
            "Settings: Toggle favorite",
            "Toggle last-run script as favorite (Ctrl+D)",
            self.action_toggle_favorite,
            discover=False,
        )
        yield SystemCommand(
            "Settings: Record/save macro",
            "Start/stop macro recording (Ctrl+M)",
            self.action_start_macro,
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
