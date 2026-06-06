"""
{
  "name": "Add Line Numbers",
  "slug": "add_line_numbers",
  "description": "Prefix each line with its number",
  "tags": ["text", "lines"],
  "bias": 0.0,
  "category": "Lines"
}
"""


def transform(text: str) -> str:
    lines = text.split("\n")
    numbered = [f"{i + 1}: {line}" for i, line in enumerate(lines)]
    return "\n".join(numbered)
