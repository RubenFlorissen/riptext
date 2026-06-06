"""
{
  "name": "Uppercase",
  "slug": "uppercase",
  "description": "Convert text to uppercase",
  "tags": ["text", "case"],
  "bias": 0.0,
  "category": "Text Case"
}
"""


def transform(text: str) -> str:
    return text.upper()
