"""
{
  "name": "Reverse Text",
  "slug": "reverse",
  "description": "Reverse the text",
  "tags": ["text"],
  "bias": 0.0,
  "category": "Text"
}
"""


def transform(text: str) -> str:
    return text[::-1]
