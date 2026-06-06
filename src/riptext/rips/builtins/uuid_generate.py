"""
{
  "name": "UUID Generate",
  "slug": "uuid_generate",
  "description": "Generate a random UUID v4",
  "tags": ["uuid", "generate", "random"],
  "aliases": ["guid"],
  "bias": 0.0,
  "category": "Utility"
}
"""

import uuid


def transform(text: str) -> str:
    return str(uuid.uuid4())
