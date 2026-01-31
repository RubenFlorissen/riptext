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


@dataclass(frozen=True)
class ScriptMetadata:
    name: str
    slug: str
    description: str
    tags: tuple[str, ...]
    bias: float
    path: Path
    source: str

    def search_tokens(self) -> Iterable[str]:
        yield self.name
        yield self.slug
        yield self.description
        yield " ".join(self.tags)
