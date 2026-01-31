from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Iterable

from .models import ScriptMetadata
from .search import rank_scripts


def _parse_metadata(text: str) -> dict:
    try:
        module = ast.parse(text)
    except SyntaxError:
        return {}
    docstring = ast.get_docstring(module)
    if not docstring:
        return {}
    try:
        return json.loads(docstring)
    except json.JSONDecodeError:
        return {}


def _metadata_from_path(path: Path, source: str) -> ScriptMetadata:
    text = path.read_text(encoding="utf-8")
    meta = _parse_metadata(text)

    slug = str(meta.get("slug") or path.stem)
    name = str(meta.get("name") or slug.replace("_", " ").title())
    description = str(meta.get("description") or "")
    tags = tuple(meta.get("tags") or [])
    bias = float(meta.get("bias") or 0.0)

    return ScriptMetadata(
        name=name,
        slug=slug,
        description=description,
        tags=tags,
        bias=bias,
        path=path,
        source=source,
    )


def _iter_script_paths(directory: Path) -> Iterable[Path]:
    if not directory.exists():
        return []
    return [
        path
        for path in directory.glob("*.py")
        if path.is_file() and not path.name.startswith("__")
    ]


def load_builtin_scripts() -> list[ScriptMetadata]:
    try:
        import riptext.rips.builtins as builtins_pkg
    except ImportError:
        return []

    package_dir = Path(builtins_pkg.__file__).parent
    return [_metadata_from_path(path, "builtin") for path in _iter_script_paths(package_dir)]


def load_user_scripts(directory: Path) -> list[ScriptMetadata]:
    return [_metadata_from_path(path, "user") for path in _iter_script_paths(directory)]


def load_all_scripts(user_dir: Path | None = None) -> list[ScriptMetadata]:
    if user_dir is None:
        user_dir = Path.home() / ".riptext" / "rips"

    scripts = {script.slug: script for script in load_builtin_scripts()}
    for script in load_user_scripts(user_dir):
        scripts[script.slug] = script
    return list(scripts.values())


class ScriptIndex:
    def __init__(self, scripts: Iterable[ScriptMetadata]) -> None:
        self._scripts = list(scripts)

    @property
    def scripts(self) -> list[ScriptMetadata]:
        return list(self._scripts)

    def search(self, query: str) -> list[ScriptMetadata]:
        if not query.strip():
            return sorted(self._scripts, key=lambda script: script.name.lower())
        matches = rank_scripts(query, self._scripts)
        return [match.script for match in matches]
