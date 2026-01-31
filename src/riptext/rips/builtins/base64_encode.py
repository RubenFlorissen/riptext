"""
{
  "name": "Base64 Encode",
  "slug": "base64_encode",
  "description": "Encode text as Base64",
  "tags": ["encoding", "base64"],
  "bias": 0.0
}
"""

import base64


def transform(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")
