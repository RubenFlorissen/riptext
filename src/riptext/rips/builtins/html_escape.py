"""
{
  "name": "HTML Escape",
  "slug": "html_escape",
  "description": "Escape text for HTML",
  "tags": ["html", "escape", "encode"],
  "aliases": ["entities"],
  "bias": 0.0,
  "category": "Encoding"
}
"""

import html


def transform(text: str) -> str:
    return html.escape(text, quote=True)
