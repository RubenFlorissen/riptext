"""
{
  "name": "URL Encode",
  "slug": "url_encode",
  "description": "URL-encode text (percent encoding)",
  "tags": ["encoding", "url"],
  "bias": 0.0
}
"""

from urllib.parse import quote


def transform(text: str) -> str:
    return quote(text, safe="")
