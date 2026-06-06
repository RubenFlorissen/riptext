"""Chained transforms (macros) for riptext."""

from __future__ import annotations

import json
from pathlib import Path

MACROS_DIR = Path.home() / ".riptext" / "macros"


def _ensure_dir() -> None:
    MACROS_DIR.mkdir(parents=True, exist_ok=True)


def list_macros() -> list[dict]:
    """Return list of macro definitions {name, slugs}."""
    _ensure_dir()
    macros = []
    for f in sorted(MACROS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            macros.append({"name": data.get("name", f.stem), "slugs": data.get("slugs", []), "path": str(f)})
        except (json.JSONDecodeError, OSError):
            continue
    return macros


def save_macro(name: str, slugs: list[str]) -> Path:
    """Save a macro to disk. Returns path."""
    _ensure_dir()
    slug = name.lower().replace(" ", "_")
    path = MACROS_DIR / f"{slug}.json"
    path.write_text(json.dumps({"name": name, "slugs": slugs}, indent=2), encoding="utf-8")
    return path


def delete_macro(name: str) -> bool:
    """Delete a macro by name. Returns True if deleted."""
    slug = name.lower().replace(" ", "_")
    path = MACROS_DIR / f"{slug}.json"
    if path.exists():
        path.unlink()
        return True
    return False
