"""
{
  "name": "Uppercase",
  "slug": "uppercase",
  "description": "Convert text to uppercase",
  "tags": ["text", "case"],
  "bias": 0.0
}
"""


def transform(text: str) -> str:
    return text.upper()
