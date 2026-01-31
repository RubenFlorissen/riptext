from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from rapidfuzz import fuzz as _fuzz_type

from .models import ScriptMetadata

# Lazy import for faster startup
_fuzz = None


def _get_fuzz():
    global _fuzz
    if _fuzz is None:
        from rapidfuzz import fuzz
        _fuzz = fuzz
    return _fuzz


@dataclass(frozen=True)
class ScriptMatch:
    script: ScriptMetadata
    score: float


def _score_field(query: str, value: str) -> float:
    if not value:
        return 0.0
    return float(_get_fuzz().WRatio(query, value))


def rank_scripts(
    query: str,
    scripts: Iterable[ScriptMetadata],
    *,
    min_score: float = 30.0,
) -> list[ScriptMatch]:
    query = query.strip()
    matches: list[ScriptMatch] = []
    for script in scripts:
        if not query:
            score = 0.0
        else:
            name_score = _score_field(query, script.name) * 3.0
            slug_score = _score_field(query, script.slug) * 2.0
            tag_score = _score_field(query, " ".join(script.tags)) * 2.0
            desc_score = _score_field(query, script.description)
            score = name_score + slug_score + tag_score + desc_score
        score += script.bias * 100.0
        if not query or score >= min_score:
            matches.append(ScriptMatch(script=script, score=score))
    matches.sort(key=lambda item: item.score, reverse=True)
    return matches
