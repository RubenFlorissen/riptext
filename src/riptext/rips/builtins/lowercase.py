"""
{
  "name": "Lowercase",
  "slug": "lowercase",
  "description": "Convert text to lowercase",
  "tags": ["text", "case"],
  "bias": 0.0
}
"""


def transform(text: str) -> str:
    return text.lower()
