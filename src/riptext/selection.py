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


def loc_to_offset(text: str, row: int, col: int) -> int:
    """Convert a TextArea location to a document offset."""
    lines = text.split("\n")
    row = max(0, min(row, len(lines) - 1))
    col = max(0, min(col, len(lines[row])))
    return sum(len(lines[i]) + 1 for i in range(row)) + col


def offset_to_loc(text: str, offset: int) -> tuple[int, int]:
    """Convert a document offset to a zero-based TextArea location."""
    lines = text.split("\n")
    offset = max(0, min(offset, len(text)))
    remaining = offset
    for row, line in enumerate(lines):
        if remaining <= len(line):
            return row, remaining
        remaining -= len(line) + 1
    return len(lines) - 1, len(lines[-1])


def current_selection(editor: TextArea) -> SelectionRange | None:
    """Return the active TextArea selection as offsets, if any."""
    text = editor.text
    sel = editor.selection
    start_offset = loc_to_offset(text, sel.start[0], sel.start[1])
    end_offset = loc_to_offset(text, sel.end[0], sel.end[1])
    selection = SelectionRange(start_offset, end_offset).normalized()
    if selection.is_empty():
        return None
    return selection


def current_line_selection(editor: TextArea) -> SelectionRange:
    """Return the current cursor line as an offset range."""
    text = editor.text
    row = editor.cursor_location[0]
    lines = text.split("\n")
    row = max(0, min(row, len(lines) - 1))
    start = sum(len(lines[i]) + 1 for i in range(row))
    end = start + len(lines[row])
    return SelectionRange(start, end)


def normalize_ranges(ranges: list[SelectionRange]) -> list[SelectionRange]:
    """Normalize, de-duplicate, and sort non-empty ranges."""
    normalized: list[SelectionRange] = []
    seen: set[tuple[int, int]] = set()
    for selection in ranges:
        current = selection.normalized()
        if current.is_empty():
            continue
        key = (current.start, current.end)
        if key in seen:
            continue
        normalized.append(current)
        seen.add(key)
    return sorted(normalized, key=lambda selection: selection.start)


def can_add_range(
    ranges: list[SelectionRange], candidate: SelectionRange
) -> tuple[bool, str | None]:
    """Check whether a range can be safely added to the marked selections."""
    candidate = candidate.normalized()
    if candidate.is_empty():
        return False, "Selection is empty."
    for current in normalize_ranges(ranges):
        if current == candidate:
            return False, "Selection is already marked."
        if current.overlaps(candidate):
            return False, "Selection overlaps an existing marked range."
    return True, None


def get_selections(
    editor: TextArea,
    mode: SelectionMode,
    marked_selections: list[SelectionRange] | None = None,
) -> list[SelectionRange]:
    """Return selection ranges based on the current mode."""
    if marked_selections:
        return normalize_ranges(marked_selections)

    if mode == "full":
        return []

    if mode == "lines":
        return [current_line_selection(editor)]

    # selection mode
    selection = current_selection(editor)
    return [] if selection is None else [selection]
