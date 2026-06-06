"""
{
  "name": "HTML Unescape",
  "slug": "html_unescape",
  "description": "Decode HTML entities",
  "tags": ["html", "unescape", "decode"],
  "aliases": ["entities"],
  "bias": 0.0,
  "category": "Encoding"
}
"""

import html


def transform(text: str) -> str:
    return html.unescape(text)
