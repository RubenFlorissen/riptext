"""File save handling for riptext."""

from __future__ import annotations

from pathlib import Path

from textual.widgets import Input, TextArea


def toggle_save_input(
    save_input: Input,
    editor: TextArea,
    file_path: Path | None,
    cwd: Path,
    show_mode_callback,
    set_status_callback,
) -> None:
    """Toggle visibility of save input."""
    if save_input.has_class("visible"):
        save_input.remove_class("visible")
        editor.focus()
        show_mode_callback()
    else:
        if file_path:
            save_input.value = str(file_path)
        else:
            save_input.value = str(cwd / "untitled.txt")
        save_input.add_class("visible")
        save_input.focus()
        set_status_callback("Enter path and press Enter to save, Esc to cancel")


def handle_save_submit(
    path_str: str,
    cwd: Path,
    editor: TextArea,
    set_status_callback,
) -> Path | None:
    """Process save submission, return new file path or None on error."""
    path = Path(path_str).expanduser()
    if not path.is_absolute():
        path = cwd / path
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(editor.text, encoding="utf-8")
        set_status_callback(f"Saved to {path}", auto_clear=True)
        return path
    except OSError as e:
        set_status_callback(f"Save failed: {e}", error=True, auto_clear=True)
        return None
