"""
{
  "name": "JSON Prettify",
  "slug": "json_prettify",
  "description": "Pretty-print JSON",
  "tags": ["json", "format"],
  "bias": 0.1
}
"""

import json


def transform(text: str) -> str:
    data = json.loads(text)
    return json.dumps(data, indent=2, sort_keys=True)
