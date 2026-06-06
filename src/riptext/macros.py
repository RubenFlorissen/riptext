"""Chained transforms (macros) for riptext."""

from __future__ import annotations

import json
from pathlib import Path
import re

MACROS_DIR = Path.home() / ".riptext" / "macros"


def macro_slug(name: str) -> str:
    """Return the stable filesystem slug for a macro name."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "macro"


def _ensure_dir() -> None:
    MACROS_DIR.mkdir(parents=True, exist_ok=True)


def list_macros() -> list[dict]:
    """Return list of macro definitions {name, slugs}."""
    _ensure_dir()
    macros = []
    for f in sorted(MACROS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            name = str(data.get("name") or f.stem)
            slugs = data.get("slugs", [])
            macros.append(
                {
                    "name": name,
                    "slug": macro_slug(name),
                    "slugs": slugs if isinstance(slugs, list) else [],
                    "path": str(f),
                }
            )
        except (json.JSONDecodeError, OSError):
            continue
    return macros


def save_macro(name: str, slugs: list[str]) -> Path:
    """Save a macro to disk. Returns path."""
    _ensure_dir()
    path = MACROS_DIR / f"{macro_slug(name)}.json"
    path.write_text(
        json.dumps({"name": name, "slugs": slugs}, indent=2),
        encoding="utf-8",
    )
    return path


def delete_macro(name: str) -> bool:
    """Delete a macro by name. Returns True if deleted."""
    path = MACROS_DIR / f"{macro_slug(name)}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def rename_macro(old_name: str, new_name: str) -> Path | None:
    """Rename a macro and its backing file. Returns the new path on success."""
    _ensure_dir()
    old_path = MACROS_DIR / f"{macro_slug(old_name)}.json"
    if not old_path.exists():
        return None

    try:
        data = json.loads(old_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    data["name"] = new_name
    new_path = MACROS_DIR / f"{macro_slug(new_name)}.json"
    new_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    if new_path != old_path:
        old_path.unlink()
    return new_path
