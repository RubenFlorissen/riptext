"""Riptext TUI application."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Sequence, cast

from textual.app import App, ComposeResult, SystemCommand
from textual.binding import Binding
from textual.widgets import Input, Label, TextArea

from .commands import RipCommandProvider
from .config import RiptextConfig
from .core.execution import run_script, run_script_sequence
from .core.models import ScriptDiagnostic, ScriptMetadata, SelectionRange
from .core.scripts import ScriptIndex, load_all_scripts, validate_scripts
from .favorites import (
    add_recent,
    remove_favorite_macro,
    rename_favorite_macro,
    toggle_favorite,
    toggle_favorite_macro,
)
from .history import TransformHistory, TransformHistoryEntry
from .macros import delete_macro, list_macros, macro_slug, rename_macro, save_macro
from .save import handle_save_submit, toggle_save_input
from .script_manager import (
    create_user_rip_template,
    ensure_user_scripts_dir,
    format_script_diagnostic,
)
from .selection import (
    MODE_LABELS,
    SelectionMode,
    can_add_range,
    cycle_mode,
    current_line_selection,
    current_selection,
    get_selections,
    normalize_ranges,
    offset_to_loc,
)
from .syntax import detect_language


CONFIGURABLE_BINDINGS: dict[str, tuple[str, str]] = {
    "open_palette": ("command_palette", "Open command palette"),
    "run_last": ("run_last", "Run last"),
    "cycle_mode": ("cycle_mode", "Cycle selection mode"),
    "save": ("save", "Save file"),
    "find": ("find", "Find"),
    "goto_line": ("goto_line", "Go to line"),
    "toggle_line_numbers": ("toggle_line_numbers", "Toggle line numbers"),
    "toggle_word_wrap": ("toggle_word_wrap", "Toggle word wrap"),
    "undo": ("undo_transform", "Undo transform"),
    "redo": ("redo_transform", "Redo transform"),
    "toggle_favorite": ("toggle_favorite", "Toggle favorite"),
    "record_macro": ("start_macro", "Record/save macro"),
    "mark_selection": ("mark_selection", "Mark selection"),
    "clear_marked_selections": (
        "clear_marked_selections",
        "Clear marked selections",
    ),
    "quit": ("quit", "Quit"),
}


class RiptextApp(App):
    """Main riptext application."""

    CSS = """
    Screen { layout: vertical; }
    #editor { height: 1fr; }
    #marked-ranges { display: none; height: 1; color: $accent; }
    #marked-ranges.visible { display: block; }
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
        Binding("ctrl+z", "undo_transform", "Undo transform", priority=True),
        Binding("ctrl+y", "redo_transform", "Redo transform", priority=True),
        Binding("ctrl+d", "toggle_favorite", "Toggle favorite", priority=True),
        Binding("ctrl+m", "start_macro", "Record/save macro", priority=True),
        Binding("ctrl+e", "mark_selection", "Mark selection", priority=True),
        Binding(
            "ctrl+u",
            "clear_marked_selections",
            "Clear marked selections",
            priority=True,
        ),
        Binding("ctrl+x", "quit", "Quit", priority=True),
        Binding("ctrl+q", "noop", show=False),
    ]

    def __init__(
        self,
        user_scripts_dir: Path | None = None,
        initial_text: str | None = None,
        file_path: Path | None = None,
        cwd: Path | None = None,
        config: RiptextConfig | None = None,
    ) -> None:
        super().__init__()
        self._config = config or RiptextConfig()
        self._user_scripts_dir = user_scripts_dir or self._config.user_rips_dir
        self._initial_text = initial_text
        self._file_path = file_path
        self._cwd = cwd or Path.cwd()
        self._index: ScriptIndex | None = None
        self._last_script: ScriptMetadata | None = None
        self._history = TransformHistory()
        self._debug_keys = os.environ.get("RIPTEXT_DEBUG_KEYS") == "1"
        self._selection_mode = cast(SelectionMode, self._config.default_mode)
        self._macro_recording: list[str] = []
        self._is_recording_macro = False
        self._macro_input_mode = "save"
        self._macro_rename_target: dict | None = None
        self._macro_preview_index = 0
        self._history_preview_index = 0
        self._marked_selections: list[SelectionRange] = []
        self._applying_transform = False
        self._status_version = 0
        self._script_diagnostics: list[ScriptDiagnostic] = []
        self._script_issue_index = 0

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield TextArea(id="editor", show_line_numbers=True)
        yield Label("", id="marked-ranges")
        default_path = str(self._file_path or self._cwd / "untitled.txt")
        yield Input(value=default_path, placeholder="File path to save...", id="save-input")
        yield Input(placeholder="Find text...", id="find-input")
        yield Input(placeholder="Go to line number...", id="goto-input")
        yield Input(placeholder="Macro name (Enter to save)...", id="macro-input")
        yield Label("", id="status")

    def on_mount(self) -> None:
        self._reload_scripts()
        editor = self.query_one("#editor", TextArea)
        editor.show_line_numbers = self._config.show_line_numbers
        editor.soft_wrap = self._config.word_wrap
        if self._initial_text:
            editor.text = self._initial_text
        self._apply_syntax_highlighting(editor)
        self._apply_config_keybindings()
        self._update_marked_ranges_indicator()
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

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Clear marked selections when manual edits may invalidate offsets."""
        if self._applying_transform or not self._marked_selections:
            return
        self._marked_selections = []
        self._update_marked_ranges_indicator()
        self._set_status("Cleared marked selections after text edit.", auto_clear=True)

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
            if self._macro_input_mode == "rename":
                self._rename_macro(event.value)
            else:
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

    def action_mark_selection(self) -> None:
        """Add the active selection, or current line, to marked selections."""
        editor = self.query_one("#editor", TextArea)
        candidate = current_selection(editor) or current_line_selection(editor)
        can_add, reason = can_add_range(self._marked_selections, candidate)
        if not can_add:
            self._set_status(
                reason or "Selection could not be marked.",
                error=True,
                auto_clear=True,
            )
            return
        self._marked_selections = normalize_ranges(
            [*self._marked_selections, candidate]
        )
        self._update_marked_ranges_indicator()
        count = len(self._marked_selections)
        self._set_status(
            f"Marked selection {count}. Run a rip to transform marked ranges.",
            auto_clear=True,
        )

    def action_clear_marked_selections(self) -> None:
        """Clear all marked selections."""
        if not self._marked_selections:
            self._set_status(
                "No marked selections to clear.",
                error=True,
                auto_clear=True,
            )
            return
        count = len(self._marked_selections)
        self._marked_selections = []
        self._update_marked_ranges_indicator()
        self._set_status(f"Cleared {count} marked selections.", auto_clear=True)

    def action_undo_transform(self) -> None:
        """Undo the most recent transform."""
        entry = self._history.undo()
        if entry is None:
            self._set_status("Nothing to undo.", error=True)
            return
        editor = self.query_one("#editor", TextArea)
        self._applying_transform = True
        try:
            editor.text = entry.before_text
        finally:
            self._applying_transform = False
        self._set_status(
            f"Undid {entry.label}. {self._history.undo_count} undo left.",
            auto_clear=True,
        )

    def action_redo_transform(self) -> None:
        """Redo the most recently undone transform."""
        entry = self._history.redo()
        if entry is None:
            self._set_status("Nothing to redo.", error=True)
            return
        editor = self.query_one("#editor", TextArea)
        self._applying_transform = True
        try:
            editor.text = entry.after_text
        finally:
            self._applying_transform = False
        self._set_status(
            f"Redid {entry.label}. {self._history.redo_count} redo left.",
            auto_clear=True,
        )

    def action_show_transform_history(self) -> None:
        """Cycle through recent transform history entries."""
        entries = self.transform_history_for_commands()
        if not entries:
            self._history_preview_index = 0
            self._set_status("No transform history yet.", error=True, auto_clear=True)
            return

        self._history_preview_index %= len(entries)
        entry = entries[self._history_preview_index]
        self._history_preview_index += 1
        self._set_status(
            f"History {self._history_preview_index}/{len(entries)}: "
            f"{entry.label} - {self.macro_step_summary(entry.slugs)}",
            auto_clear=10.0,
        )

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

    def _apply_config_keybindings(self) -> None:
        """Add configured key aliases for supported actions."""
        for name, keys in self._config.keybindings.items():
            binding = CONFIGURABLE_BINDINGS.get(name)
            if binding is None:
                continue
            action, description = binding
            self.bind(keys, action, description=description)

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
            self._macro_input_mode = "save"
            self._macro_rename_target = None
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

    def action_show_macros(self) -> None:
        """Cycle through saved macros and show their steps."""
        macros = list_macros()
        if not macros:
            self._macro_preview_index = 0
            self._set_status("No saved macros.", error=True, auto_clear=True)
            return

        self._macro_preview_index %= len(macros)
        macro = macros[self._macro_preview_index]
        self._macro_preview_index += 1
        steps = self.macro_step_summary(macro["slugs"])
        self._set_status(
            f"Macro {self._macro_preview_index}/{len(macros)}: "
            f"{macro['name']} - {steps}",
            auto_clear=10.0,
        )

    def prompt_rename_macro(self, macro: dict) -> None:
        """Prompt for a new macro name."""
        self._hide_all_inputs()
        self._macro_input_mode = "rename"
        self._macro_rename_target = macro
        macro_input = self.query_one("#macro-input", Input)
        macro_input.value = macro["name"]
        macro_input.add_class("visible")
        macro_input.focus()
        self._set_status(f"Rename macro '{macro['name']}' and press Enter.")

    def _rename_macro(self, new_name: str) -> None:
        """Rename the macro selected by prompt_rename_macro."""
        target = self._macro_rename_target
        self._macro_input_mode = "save"
        self._macro_rename_target = None
        new_name = new_name.strip()
        if target is None or not new_name:
            self._set_status("Macro rename cancelled.", auto_clear=True)
            return

        old_slug = target["slug"]
        path = rename_macro(target["name"], new_name)
        if path is None:
            self._set_status(
                f"Could not rename macro '{target['name']}'.",
                error=True,
                auto_clear=True,
            )
            return
        rename_favorite_macro(old_slug, macro_slug(new_name))
        self._set_status(
            f"Renamed macro '{target['name']}' to '{new_name}'.",
            auto_clear=True,
        )

    def delete_saved_macro(self, macro: dict) -> None:
        """Delete a saved macro."""
        if delete_macro(macro["name"]):
            remove_favorite_macro(macro["slug"])
            self._set_status(f"Deleted macro '{macro['name']}'.", auto_clear=True)
        else:
            self._set_status(
                f"Could not delete macro '{macro['name']}'.",
                error=True,
                auto_clear=True,
            )

    def toggle_saved_macro_favorite(self, macro: dict) -> None:
        """Toggle favorite state for a saved macro."""
        is_fav = toggle_favorite_macro(macro["slug"])
        label = "Favorited" if is_fav else "Unfavorited"
        self._set_status(f"{label} macro: {macro['name']}", auto_clear=True)

    def preview_macro(self, macro: dict) -> None:
        """Show a saved macro's steps."""
        self._set_status(
            f"Macro '{macro['name']}': {self.macro_step_summary(macro['slugs'])}",
            auto_clear=10.0,
        )

    def action_validate_scripts(self) -> None:
        """Validate built-in and user scripts."""
        self._script_diagnostics = validate_scripts(self._user_scripts_dir)
        self._script_issue_index = 0
        if not self._script_diagnostics:
            self._set_status("All scripts validated cleanly.", auto_clear=True)
            return

        errors = sum(
            diagnostic.severity == "error"
            for diagnostic in self._script_diagnostics
        )
        warnings = sum(
            diagnostic.severity == "warning"
            for diagnostic in self._script_diagnostics
        )
        first = self._script_diagnostics[0]
        self._set_status(
            f"Scripts: {errors} errors, {warnings} warnings. "
            f"First: {first.path.name}: {first.message}",
            error=errors > 0,
            auto_clear=8.0,
        )

    def action_show_script_issues(self) -> None:
        """Show the next script validation issue."""
        self._script_diagnostics = validate_scripts(self._user_scripts_dir)
        if not self._script_diagnostics:
            self._script_issue_index = 0
            self._set_status("No script validation issues.", auto_clear=True)
            return

        self._script_issue_index %= len(self._script_diagnostics)
        issue = self._script_diagnostics[self._script_issue_index]
        self._script_issue_index += 1
        self._set_status(
            format_script_diagnostic(
                issue,
                index=self._script_issue_index,
                total=len(self._script_diagnostics),
            ),
            error=issue.severity == "error",
            auto_clear=10.0,
        )

    def action_reload_scripts(self) -> None:
        """Reload built-in and user scripts."""
        self._reload_scripts()
        script_count = len(self._index.scripts) if self._index else 0
        issue_count = len(self._script_diagnostics)
        if issue_count:
            self._set_status(
                f"Reloaded {script_count} scripts with {issue_count} validation issues.",
                error=any(
                    diagnostic.severity == "error"
                    for diagnostic in self._script_diagnostics
                ),
                auto_clear=8.0,
            )
        else:
            self._set_status(f"Reloaded {script_count} scripts.", auto_clear=True)

    def action_show_user_rips_dir(self) -> None:
        """Show the user rips directory."""
        user_dir = ensure_user_scripts_dir(self._user_scripts_dir)
        self._set_status(f"User rips directory: {user_dir}", auto_clear=10.0)

    def action_create_user_rip(self) -> None:
        """Create a starter user rip template."""
        path = create_user_rip_template(self._user_scripts_dir)
        self._reload_scripts()
        self._set_status(f"Created rip template: {path}", auto_clear=10.0)

    # -------------------------------------------------------------------------
    # Scripts
    # -------------------------------------------------------------------------

    def _reload_scripts(self) -> None:
        scripts = load_all_scripts(self._user_scripts_dir)
        self._index = ScriptIndex(scripts)
        self._script_diagnostics = validate_scripts(self._user_scripts_dir)
        self._script_issue_index = 0

    def reload_scripts(self) -> None:
        """Public method for hot-reloading scripts."""
        self._reload_scripts()

    def scripts_for_commands(self) -> list[ScriptMetadata]:
        if not self._index:
            return []
        return sorted(self._index.scripts, key=lambda s: s.name.lower())

    def transform_history_for_commands(self) -> list[TransformHistoryEntry]:
        """Return recent transforms that can be re-run from the palette."""
        return self._history.recent()[:10]

    def _record_transform(
        self,
        label: str,
        slugs: Sequence[str],
        before_text: str,
        after_text: str,
    ) -> None:
        self._history.record(
            TransformHistoryEntry(
                label=label,
                slugs=tuple(slugs),
                before_text=before_text,
                after_text=after_text,
            )
        )

    def rerun_history_entry(self, entry: TransformHistoryEntry) -> None:
        """Re-run a transform history entry on the current editor state."""
        if not entry.slugs:
            self._set_status(
                f"History entry '{entry.label}' has no scripts.",
                error=True,
                auto_clear=True,
            )
            return

        if len(entry.slugs) == 1:
            script = self._find_script_by_slug(entry.slugs[0])
            if script is None:
                self._set_status(
                    f"Script '{entry.slugs[0]}' not found.",
                    error=True,
                    auto_clear=True,
                )
                return
            self.run_script(script)
            return

        self.run_macro(list(entry.slugs), macro_name=entry.label)

    def run_script(self, script: ScriptMetadata) -> None:
        editor = self.query_one("#editor", TextArea)

        # Handle special detect_language script
        if script.slug == "detect_language":
            self._run_detect_language(editor)
            return

        text = editor.text
        selections = get_selections(
            editor,
            self._selection_mode,
            self._marked_selections,
        )
        marked_count = len(self._marked_selections)
        new_text, info, errors = run_script(script, text, selections)
        self._applying_transform = True
        try:
            editor.text = new_text
        finally:
            self._applying_transform = False
        self._last_script = script
        if marked_count:
            self._marked_selections = []
            self._update_marked_ranges_indicator()
        self._record_transform(script.name, [script.slug], text, new_text)

        # Track usage
        add_recent(script.slug)
        if self._is_recording_macro:
            self._macro_recording.append(script.slug)

        if errors:
            self._set_status(errors[-1], error=True, auto_clear=True)
        elif info:
            self._set_status(info[-1], auto_clear=6.0)
        else:
            rec = " 🔴" if self._is_recording_macro else ""
            target = f" on {marked_count} selections" if marked_count else ""
            self._set_status(f"Ran {script.name}{target}.{rec}", auto_clear=True)

    def macro_step_summary(self, slugs: Sequence[str]) -> str:
        """Return human-readable script names for a macro chain."""
        names: list[str] = []
        for slug in slugs:
            script = self._find_script_by_slug(slug)
            names.append(script.name if script else slug)
        return " -> ".join(names) if names else "No steps"

    def run_saved_macro(self, macro: dict) -> None:
        """Run a saved macro definition."""
        self.run_macro(macro["slugs"], macro_name=macro["name"])

    def run_macro(self, slugs: list[str], macro_name: str | None = None) -> None:
        """Run a sequence of scripts (macro)."""
        editor = self.query_one("#editor", TextArea)
        before_text = editor.text

        all_errors: list[str] = []
        scripts: list[ScriptMetadata] = []
        for slug in slugs:
            script = self._find_script_by_slug(slug)
            if not script:
                all_errors.append(f"Script '{slug}' not found")
                continue
            scripts.append(script)

        if not scripts:
            message = all_errors[-1] if all_errors else "Macro has no scripts."
            self._set_status(message, error=True, auto_clear=True)
            return

        if self._marked_selections:
            selections = get_selections(
                editor,
                self._selection_mode,
                self._marked_selections,
            )
            marked_count = len(self._marked_selections)
            new_text, _, errors = run_script_sequence(scripts, editor.text, selections)
            self._applying_transform = True
            try:
                editor.text = new_text
            finally:
                self._applying_transform = False
            self._marked_selections = []
            self._update_marked_ranges_indicator()
            label = macro_name or "Macro"
            self._record_transform(label, slugs, before_text, new_text)
            all_errors.extend(errors)
            if all_errors:
                self._set_status(all_errors[-1], error=True, auto_clear=True)
            else:
                label = f"'{macro_name}' " if macro_name else ""
                self._set_status(
                    f"Macro {label}complete: {self.macro_step_summary(slugs)} "
                    f"on {marked_count} selections.",
                    auto_clear=True,
                )
            return

        for script in scripts:
            selections = get_selections(editor, self._selection_mode)
            new_text, _, errors = run_script(script, editor.text, selections)
            self._applying_transform = True
            try:
                editor.text = new_text
            finally:
                self._applying_transform = False
            all_errors.extend(errors)

        label = macro_name or "Macro"
        self._record_transform(label, slugs, before_text, editor.text)
        if all_errors:
            self._set_status(all_errors[-1], error=True, auto_clear=True)
        else:
            label = f"'{macro_name}' " if macro_name else ""
            self._set_status(
                f"Macro {label}complete: {self.macro_step_summary(slugs)}.",
                auto_clear=True,
            )

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

    def _format_marked_range(self, text: str, selection: SelectionRange) -> str:
        """Return a compact one-based line/column label for a marked range."""
        current = selection.normalized()
        start_row, start_col = offset_to_loc(text, current.start)
        end_row, end_col = offset_to_loc(text, current.end)
        return (
            f"L{start_row + 1}:C{start_col + 1}-"
            f"L{end_row + 1}:C{end_col + 1}"
        )

    def _update_marked_ranges_indicator(self) -> None:
        """Show or hide the marked range indicator strip."""
        label = self.query_one("#marked-ranges", Label)
        if not self._marked_selections:
            label.update("")
            label.remove_class("visible")
            return

        editor = self.query_one("#editor", TextArea)
        ranges = [
            self._format_marked_range(editor.text, selection)
            for selection in self._marked_selections[:4]
        ]
        remaining = len(self._marked_selections) - len(ranges)
        suffix = f" | +{remaining} more" if remaining else ""
        label.update(f"Marked ranges: {' | '.join(ranges)}{suffix}")
        label.add_class("visible")

    def _set_status(
        self, message: str, *, error: bool = False, auto_clear: bool | float = False
    ) -> None:
        self._status_version += 1
        status_version = self._status_version
        label = self.query_one("#status", Label)
        label.update(message)
        label.styles.color = "red" if error else "white"
        if auto_clear:
            delay = 2.0 if auto_clear is True else float(auto_clear)

            def clear_if_current() -> None:
                if self._status_version == status_version:
                    self._show_mode()

            self.set_timer(delay, clear_if_current)

    def _show_mode(self) -> None:
        self._update_marked_ranges_indicator()
        marked = (
            f" | Marked: {len(self._marked_selections)}"
            if self._marked_selections
            else ""
        )
        self._set_status(
            f"Mode: {MODE_LABELS[self._selection_mode]}{marked} (Ctrl+L to change)"
        )

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
            "History: Redo transform",
            "Redo the most recently undone transform (Ctrl+Y)",
            self.action_redo_transform,
            discover=False,
        )
        yield SystemCommand(
            "History: Show transform history",
            "Cycle through recent transform history entries",
            self.action_show_transform_history,
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
        yield SystemCommand(
            "Macros: Show saved macros",
            "Cycle through saved macros and show their steps",
            self.action_show_macros,
            discover=False,
        )
        yield SystemCommand(
            "Settings: Mark selection",
            "Add active selection, or current line, to marked transform ranges (Ctrl+E)",
            self.action_mark_selection,
            discover=False,
        )
        yield SystemCommand(
            "Settings: Clear marked selections",
            "Clear all marked transform ranges (Ctrl+U)",
            self.action_clear_marked_selections,
            discover=False,
        )
        yield SystemCommand(
            "Settings: Validate scripts",
            "Check built-in and user scripts for metadata and entrypoint issues",
            self.action_validate_scripts,
            discover=False,
        )
        yield SystemCommand(
            "Scripts: Show script issues",
            "Cycle through validation issues for built-in and user scripts",
            self.action_show_script_issues,
            discover=False,
        )
        yield SystemCommand(
            "Scripts: Reload scripts",
            "Reload built-in and user rips from disk",
            self.action_reload_scripts,
            discover=False,
        )
        yield SystemCommand(
            "Scripts: Show user rips directory",
            "Show the path where user rips are loaded from",
            self.action_show_user_rips_dir,
            discover=False,
        )
        yield SystemCommand(
            "Scripts: Create user rip template",
            "Create a starter Python rip in the user rips directory",
            self.action_create_user_rip,
            discover=False,
        )


def run_app(
    user_scripts_dir: Path | None = None,
    initial_text: str | None = None,
    file_path: Path | None = None,
    cwd: Path | None = None,
    config: RiptextConfig | None = None,
) -> None:
    """Entry point to run the application."""
    RiptextApp(
        user_scripts_dir,
        initial_text=initial_text,
        file_path=file_path,
        cwd=cwd,
        config=config,
    ).run()
