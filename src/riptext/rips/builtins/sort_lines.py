"""
{
  "name": "Sort Lines",
  "slug": "sort_lines",
  "description": "Sort lines alphabetically",
  "tags": ["text", "lines", "sort"],
  "bias": 0.0
}
"""


def transform(text: str) -> str:
    lines = text.split("\n")
    return "\n".join(sorted(lines))
