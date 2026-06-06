from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Iterable

from .models import ScriptDiagnostic, ScriptMetadata
from .search import rank_scripts

# Category inference from tags
_TAG_CATEGORY_MAP: dict[str, str] = {
    "json": "Data",
    "csv": "Data",
    "xml": "Data",
    "yaml": "Data",
    "format": "Formatting",
    "case": "Text Case",
    "encode": "Encoding",
    "decode": "Encoding",
    "base64": "Encoding",
    "url": "Encoding",
    "hash": "Hashing",
    "lines": "Lines",
    "sort": "Lines",
    "stats": "Analysis",
    "count": "Analysis",
    "markdown": "Formatting",
    "text": "Text",
    "transform": "Text",
}


def _infer_category(tags: tuple[str, ...]) -> str:
    """Infer a category from tags. Uses first matching tag."""
    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower in _TAG_CATEGORY_MAP:
            return _TAG_CATEGORY_MAP[tag_lower]
    return "Other"


def _parse_module(text: str) -> ast.Module | None:
    try:
        return ast.parse(text)
    except SyntaxError:
        return None


def _parse_metadata(text: str) -> tuple[dict, str | None]:
    module = _parse_module(text)
    if module is None:
        return {}, "Script has invalid Python syntax."
    docstring = ast.get_docstring(module)
    if not docstring:
        return {}, "Script is missing JSON metadata docstring."
    try:
        meta = json.loads(docstring)
    except json.JSONDecodeError as exc:
        return {}, f"Script metadata is invalid JSON: {exc.msg}."
    if not isinstance(meta, dict):
        return {}, "Script metadata must be a JSON object."
    return meta, None


def _has_entrypoint(text: str) -> bool:
    module = _parse_module(text)
    if module is None:
        return False
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name in {"main", "transform"}:
            return True
    return False


def _metadata_from_path(path: Path, source: str) -> ScriptMetadata:
    text = path.read_text(encoding="utf-8")
    meta, _ = _parse_metadata(text)

    slug = str(meta.get("slug") or path.stem)
    name = str(meta.get("name") or slug.replace("_", " ").title())
    description = str(meta.get("description") or "")
    raw_tags = meta.get("tags") or []
    tags = (
        tuple(str(tag) for tag in raw_tags)
        if isinstance(raw_tags, (list, tuple))
        else ()
    )
    raw_aliases = meta.get("aliases") or []
    aliases = (
        tuple(str(alias) for alias in raw_aliases)
        if isinstance(raw_aliases, (list, tuple))
        else ()
    )
    try:
        bias = float(meta.get("bias") or 0.0)
    except (TypeError, ValueError):
        bias = 0.0
    category = str(meta.get("category") or _infer_category(tags))

    return ScriptMetadata(
        name=name,
        slug=slug,
        description=description,
        tags=tags,
        bias=bias,
        path=path,
        source=source,
        category=category,
        aliases=aliases,
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


def _ensure_user_dir(directory: Path) -> None:
    """Create user scripts directory if it doesn't exist."""
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)


def load_all_scripts(user_dir: Path | None = None) -> list[ScriptMetadata]:
    if user_dir is None:
        user_dir = Path.home() / ".riptext" / "rips"

    _ensure_user_dir(user_dir)

    scripts = {script.slug: script for script in load_builtin_scripts()}
    for script in load_user_scripts(user_dir):
        scripts[script.slug] = script
    return list(scripts.values())


def validate_scripts(user_dir: Path | None = None) -> list[ScriptDiagnostic]:
    """Validate script files and return diagnostics without executing scripts."""
    if user_dir is None:
        user_dir = Path.home() / ".riptext" / "rips"

    _ensure_user_dir(user_dir)

    diagnostics: list[ScriptDiagnostic] = []
    seen_slugs: dict[str, ScriptMetadata] = {}

    def validate_path(path: Path, source: str) -> ScriptMetadata | None:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            diagnostics.append(
                ScriptDiagnostic(
                    "error",
                    f"Could not read script: {exc}",
                    path,
                    source,
                )
            )
            return None

        meta, metadata_error = _parse_metadata(text)
        if metadata_error:
            diagnostics.append(
                ScriptDiagnostic("warning", metadata_error, path, source)
            )

        script = _metadata_from_path(path, source)
        if not script.slug.strip():
            diagnostics.append(
                ScriptDiagnostic(
                    "error",
                    "Script slug cannot be empty.",
                    path,
                    source,
                    script.slug,
                )
            )
        if not script.name.strip():
            diagnostics.append(
                ScriptDiagnostic(
                    "warning",
                    "Script name is empty.",
                    path,
                    source,
                    script.slug,
                )
            )
        if not isinstance(meta.get("tags", []), list):
            diagnostics.append(
                ScriptDiagnostic(
                    "warning",
                    "Script tags should be a JSON array.",
                    path,
                    source,
                    script.slug,
                )
            )
        if not isinstance(meta.get("aliases", []), list):
            diagnostics.append(
                ScriptDiagnostic(
                    "warning",
                    "Script aliases should be a JSON array.",
                    path,
                    source,
                    script.slug,
                )
            )
        try:
            float(meta.get("bias", 0.0) or 0.0)
        except (TypeError, ValueError):
            diagnostics.append(
                ScriptDiagnostic(
                    "warning",
                    "Script bias should be numeric.",
                    path,
                    source,
                    script.slug,
                )
            )
        if not _has_entrypoint(text):
            diagnostics.append(
                ScriptDiagnostic(
                    "error",
                    "Script has no main() or transform() entrypoint.",
                    path,
                    source,
                    script.slug,
                )
            )

        existing = seen_slugs.get(script.slug)
        if existing is not None:
            diagnostics.append(
                ScriptDiagnostic(
                    "warning",
                    f"Duplicate slug '{script.slug}' also defined in {existing.path}.",
                    path,
                    source,
                    script.slug,
                )
            )
        seen_slugs[script.slug] = script
        return script

    try:
        import riptext.rips.builtins as builtins_pkg
    except ImportError:
        package_dir = None
    else:
        package_dir = Path(builtins_pkg.__file__).parent

    if package_dir is not None:
        for path in _iter_script_paths(package_dir):
            validate_path(path, "builtin")

    for path in _iter_script_paths(user_dir):
        validate_path(path, "user")

    return diagnostics


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
