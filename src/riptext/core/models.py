from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SelectionRange:
    start: int
    end: int

    def normalized(self) -> "SelectionRange":
        if self.start <= self.end:
            return self
        return SelectionRange(self.end, self.start)

    def is_empty(self) -> bool:
        return self.start == self.end

    def overlaps(self, other: "SelectionRange") -> bool:
        current = self.normalized()
        candidate = other.normalized()
        return current.start < candidate.end and candidate.start < current.end


@dataclass(frozen=True)
class ScriptMetadata:
    name: str
    slug: str
    description: str
    tags: tuple[str, ...]
    bias: float
    path: Path
    source: str
    category: str = "Other"
    aliases: tuple[str, ...] = ()

    def search_tokens(self) -> Iterable[str]:
        yield self.name
        yield self.slug
        yield self.description
        yield " ".join(self.tags)
        yield self.category
        yield " ".join(self.aliases)


@dataclass(frozen=True)
class ScriptDiagnostic:
    severity: str
    message: str
    path: Path
    source: str
    slug: str | None = None
