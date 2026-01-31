"""
{
  "name": "URL Decode",
  "slug": "url_decode",
  "description": "Decode URL-encoded text",
  "tags": ["encoding", "url"],
  "bias": 0.0
}
"""

from urllib.parse import unquote


def transform(text: str) -> str:
    return unquote(text)
