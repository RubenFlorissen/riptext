"""
{
  "name": "Trim Whitespace",
  "slug": "trim",
  "description": "Remove leading and trailing whitespace",
  "tags": ["text", "whitespace"],
  "bias": 0.0,
  "category": "Lines"
}
"""


def transform(text: str) -> str:
    return text.strip()
