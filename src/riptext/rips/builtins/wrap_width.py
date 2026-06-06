"""
{
  "name": "Word Wrap by Width",
  "slug": "wrap_width",
  "description": "Wrap text using an optional first-line width",
  "tags": ["wrap", "format", "text"],
  "aliases": ["word wrap"],
  "bias": 0.0,
  "category": "Formatting"
}
"""

import textwrap


def transform(text: str) -> str:
    first, separator, rest = text.partition("\n")
    if separator and first.strip().isdigit():
        width = max(1, int(first.strip()))
        body = rest
    else:
        width = 80
        body = text
    return "\n\n".join(
        textwrap.fill(paragraph, width=width)
        for paragraph in body.split("\n\n")
    )
