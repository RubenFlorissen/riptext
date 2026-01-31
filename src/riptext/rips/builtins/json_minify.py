"""
{
  "name": "JSON Minify",
  "slug": "json_minify",
  "description": "Minify JSON by removing whitespace",
  "tags": ["json", "minify", "compact"],
  "bias": 0.0
}
"""

import json


def main(exec):
    try:
        data = json.loads(exec.text)
        exec.insert(json.dumps(data, separators=(",", ":")))
    except json.JSONDecodeError as e:
        exec.post_error(f"Invalid JSON: {e}")
