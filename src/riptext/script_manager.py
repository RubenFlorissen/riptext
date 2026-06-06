"""User rip management helpers."""

from __future__ import annotations

import re
from pathlib import Path

from .core.models import ScriptDiagnostic

DEFAULT_USER_RIPS_DIR = Path.home() / ".riptext" / "rips"


def resolve_user_scripts_dir(directory: Path | None = None) -> Path:
    """Return the configured user scripts directory."""
    return directory or DEFAULT_USER_RIPS_DIR


def ensure_user_scripts_dir(directory: Path | None = None) -> Path:
    """Create and return the user scripts directory."""
    user_dir = resolve_user_scripts_dir(directory)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def slugify_name(name: str) -> str:
    """Convert a display name to a simple rip slug."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    return slug or "new_rip"


def _unique_template_path(directory: Path, slug: str) -> tuple[Path, str]:
    path = directory / f"{slug}.py"
    if not path.exists():
        return path, slug

    index = 2
    while True:
        candidate_slug = f"{slug}_{index}"
        path = directory / f"{candidate_slug}.py"
        if not path.exists():
            return path, candidate_slug
        index += 1


def create_user_rip_template(
    directory: Path | None = None,
    *,
    name: str = "New Rip",
) -> Path:
    """Create a starter user rip template and return its path."""
    user_dir = ensure_user_scripts_dir(directory)
    slug = slugify_name(name)
    path, final_slug = _unique_template_path(user_dir, slug)
    display_name = final_slug.replace("_", " ").title()
    content = f'''"""
{{
  "name": "{display_name}",
  "slug": "{final_slug}",
  "description": "Describe what this rip does",
  "tags": ["custom"],
  "category": "Custom",
  "bias": 0.0
}}
"""


def main(exec):
    text = exec.text
    exec.insert(text)
    exec.post_info("Ran {display_name}")
'''
    path.write_text(content, encoding="utf-8")
    return path


def format_script_diagnostic(
    diagnostic: ScriptDiagnostic,
    *,
    index: int,
    total: int,
) -> str:
    """Format a diagnostic for the one-line status bar."""
    label = diagnostic.severity.upper()
    slug = f" [{diagnostic.slug}]" if diagnostic.slug else ""
    return (
        f"{index}/{total} {label}{slug} {diagnostic.path.name}: "
        f"{diagnostic.message}"
    )
