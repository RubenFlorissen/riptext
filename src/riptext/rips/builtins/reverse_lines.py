"""
{
  "name": "Reverse Lines",
  "slug": "reverse_lines",
  "description": "Reverse the order of lines",
  "tags": ["text", "lines"],
  "bias": 0.0
}
"""


def transform(text: str) -> str:
    lines = text.split("\n")
    return "\n".join(reversed(lines))
