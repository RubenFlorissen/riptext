"""Favorites and recently used scripts tracking for riptext."""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_STATE_DIR = Path.home() / ".riptext"
STATE_FILE = DEFAULT_STATE_DIR / "state.json"
MAX_RECENT = 10


def _load_state() -> dict:
    """Load state from disk."""
    if not STATE_FILE.exists():
        return {"favorites": [], "recent": []}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"favorites": [], "recent": []}


def _save_state(state: dict) -> None:
    """Save state to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def get_favorites() -> list[str]:
    """Return list of favorite script slugs."""
    return _load_state().get("favorites", [])


def toggle_favorite(slug: str) -> bool:
    """Toggle a script as favorite. Returns True if now a favorite."""
    state = _load_state()
    favorites = state.get("favorites", [])
    if slug in favorites:
        favorites.remove(slug)
        is_fav = False
    else:
        favorites.append(slug)
        is_fav = True
    state["favorites"] = favorites
    _save_state(state)
    return is_fav


def get_recent() -> list[str]:
    """Return list of recently used script slugs (most recent first)."""
    return _load_state().get("recent", [])


def add_recent(slug: str) -> None:
    """Add a script to the recent list."""
    state = _load_state()
    recent = state.get("recent", [])
    if slug in recent:
        recent.remove(slug)
    recent.insert(0, slug)
    state["recent"] = recent[:MAX_RECENT]
    _save_state(state)


def get_script_priority(slug: str) -> tuple[int, int, int]:
    """Return sort key for a script: (favorite_rank, recent_rank).
    
    Lower = higher priority. Favorites come first, then recent, then rest.
    """
    state = _load_state()
    favorites = state.get("favorites", [])
    recent = state.get("recent", [])

    fav_rank = favorites.index(slug) if slug in favorites else 999
    recent_rank = recent.index(slug) if slug in recent else 999

    return (0 if slug in favorites else 1, fav_rank, recent_rank)
