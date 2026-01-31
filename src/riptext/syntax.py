"""Syntax highlighting and language detection for riptext."""

from __future__ import annotations

import re
from pathlib import Path

# Map file extensions to TextArea language names
EXTENSION_MAP: dict[str, str] = {
    ".py": "python",
    ".pyw": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "javascript",
    ".tsx": "javascript",
    ".jsx": "javascript",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".md": "markdown",
    ".markdown": "markdown",
    ".html": "html",
    ".htm": "html",
    ".xml": "xml",
    ".svg": "xml",
    ".css": "css",
    ".scss": "css",
    ".sql": "sql",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".fish": "bash",
}

# Patterns to detect language from content
CONTENT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\s*<\?xml", re.MULTILINE), "xml"),
    (re.compile(r"^\s*<!DOCTYPE\s+html", re.IGNORECASE | re.MULTILINE), "html"),
    (re.compile(r"^\s*<html", re.IGNORECASE | re.MULTILINE), "html"),
    (re.compile(r"^#!.*python", re.MULTILINE), "python"),
    (re.compile(r"^#!.*\b(ba)?sh\b", re.MULTILINE), "bash"),
    (re.compile(r"^\s*\{[\s\n]*\"", re.MULTILINE), "json"),
    (re.compile(r"^\s*\[[\s\n]*\{", re.MULTILINE), "json"),
    (re.compile(r"^---\s*$", re.MULTILINE), "yaml"),
    (re.compile(r"^\s*def\s+\w+\s*\(", re.MULTILINE), "python"),
    (re.compile(r"^\s*class\s+\w+.*:", re.MULTILINE), "python"),
    (re.compile(r"^\s*import\s+\w+", re.MULTILINE), "python"),
    (re.compile(r"^\s*from\s+\w+\s+import", re.MULTILINE), "python"),
    (re.compile(r"^\s*(const|let|var|function)\s+\w+", re.MULTILINE), "javascript"),
    (re.compile(r"^\s*export\s+(default\s+)?(function|class|const)", re.MULTILINE), "javascript"),
    (re.compile(r"^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\s+", re.IGNORECASE | re.MULTILINE), "sql"),
    (re.compile(r"^\s*#\s+", re.MULTILINE), "markdown"),
    (re.compile(r"^\[[\w.-]+\]", re.MULTILINE), "toml"),
    (re.compile(r"^\s*fn\s+\w+", re.MULTILINE), "rust"),
    (re.compile(r"^\s*func\s+\w+", re.MULTILINE), "go"),
    (re.compile(r"^\s*package\s+\w+;", re.MULTILINE), "java"),
]

# Available languages in Textual's TextArea
AVAILABLE_LANGUAGES = {
    "css", "java", "go", "regex", "bash", "toml", "javascript",
    "yaml", "sql", "json", "rust", "html", "python", "markdown", "xml"
}


def detect_language_from_path(path: Path | None) -> str | None:
    """Detect language from file extension."""
    if path is None:
        return None
    suffix = path.suffix.lower()
    lang = EXTENSION_MAP.get(suffix)
    if lang and lang in AVAILABLE_LANGUAGES:
        return lang
    return None


def detect_language_from_content(text: str) -> str | None:
    """Detect language from content patterns."""
    if not text or len(text) < 3:
        return None
    
    # Only check the first 2000 chars for performance
    sample = text[:2000]
    
    for pattern, lang in CONTENT_PATTERNS:
        if pattern.search(sample):
            if lang in AVAILABLE_LANGUAGES:
                return lang
    
    return None


def detect_language(path: Path | None, text: str) -> str | None:
    """Detect language from path first, then content."""
    lang = detect_language_from_path(path)
    if lang:
        return lang
    return detect_language_from_content(text)
