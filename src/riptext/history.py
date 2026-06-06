"""Runtime transform history for undo, redo, and re-run."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransformHistoryEntry:
    label: str
    slugs: tuple[str, ...]
    before_text: str
    after_text: str


class TransformHistory:
    """Bounded transform history with separate undo and redo stacks."""

    def __init__(self, max_entries: int = 50) -> None:
        self.max_entries = max_entries
        self._undo: list[TransformHistoryEntry] = []
        self._redo: list[TransformHistoryEntry] = []

    def record(self, entry: TransformHistoryEntry) -> bool:
        """Record a transform. Returns False for no-op text changes."""
        if entry.before_text == entry.after_text:
            return False

        self._undo.append(entry)
        if len(self._undo) > self.max_entries:
            del self._undo[0 : len(self._undo) - self.max_entries]
        self._redo.clear()
        return True

    def undo(self) -> TransformHistoryEntry | None:
        if not self._undo:
            return None
        entry = self._undo.pop()
        self._redo.append(entry)
        return entry

    def redo(self) -> TransformHistoryEntry | None:
        if not self._redo:
            return None
        entry = self._redo.pop()
        self._undo.append(entry)
        return entry

    def recent(self) -> list[TransformHistoryEntry]:
        """Return recent transforms, newest first."""
        return list(reversed(self._undo))

    @property
    def undo_count(self) -> int:
        return len(self._undo)

    @property
    def redo_count(self) -> int:
        return len(self._redo)
