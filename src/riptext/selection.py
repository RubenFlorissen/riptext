"""Selection mode handling for riptext."""

from __future__ import annotations

from typing import Literal

from textual.widgets import TextArea

from .core.models import SelectionRange

SelectionMode = Literal["full", "lines", "selection"]

MODE_LABELS: dict[SelectionMode, str] = {
    "full": "Full text",
    "lines": "Current line",
    "selection": "Selection",
}

MODES: list[SelectionMode] = ["full", "lines", "selection"]


def cycle_mode(current: SelectionMode) -> SelectionMode:
    idx = MODES.index(current)
    return MODES[(idx + 1) % len(MODES)]


def get_selections(editor: TextArea, mode: SelectionMode) -> list[SelectionRange]:
    """Return selection ranges based on the current mode."""
    text = editor.text

    if mode == "full":
        return []

    if mode == "lines":
        cursor = editor.cursor_location
        row = cursor[0]
        lines = text.split("\n")
        start = sum(len(lines[i]) + 1 for i in range(row))
        end = start + len(lines[row]) if row < len(lines) else start
        return [SelectionRange(start, end)]

    # selection mode
    sel = editor.selection
    start_loc = sel.start
    end_loc = sel.end
    lines = text.split("\n")

    def loc_to_offset(row: int, col: int) -> int:
        offset = sum(len(lines[i]) + 1 for i in range(row))
        return offset + col

    start_offset = loc_to_offset(start_loc[0], start_loc[1])
    end_offset = loc_to_offset(end_loc[0], end_loc[1])
    if start_offset == end_offset:
        return []
    return [SelectionRange(min(start_offset, end_offset), max(start_offset, end_offset))]
