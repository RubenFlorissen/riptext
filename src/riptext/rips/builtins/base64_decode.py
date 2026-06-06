"""
{
  "name": "Base64 Decode",
  "slug": "base64_decode",
  "description": "Decode Base64 text",
  "tags": ["encoding", "base64"],
  "bias": 0.0,
  "category": "Encoding"
}
"""

import base64


def transform(text: str) -> str:
    return base64.b64decode(text.encode("ascii")).decode("utf-8")
