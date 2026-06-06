"""
{
  "name": "Slugify",
  "slug": "slugify",
  "description": "Convert text to a URL-friendly slug",
  "tags": ["slug", "url", "case"],
  "aliases": ["permalink"],
  "bias": 0.0,
  "category": "Text Case"
}
"""

import re
import unicodedata


def transform(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)
