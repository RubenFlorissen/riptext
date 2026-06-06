"""
{
  "name": "Lowercase",
  "slug": "lowercase",
  "description": "Convert text to lowercase",
  "tags": ["text", "case"],
  "bias": 0.0,
  "category": "Text Case"
}
"""


def transform(text: str) -> str:
    return text.lower()
