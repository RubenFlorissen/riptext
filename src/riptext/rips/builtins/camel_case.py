"""
{
  "name": "camelCase",
  "slug": "camel_case",
  "description": "Convert to camelCase",
  "tags": ["case", "camel", "format"],
  "bias": 0.0,
  "category": "Text Case"
}
"""

import re


def main(exec):
    text = exec.text.strip()
    # Split on non-alphanumeric characters
    words = re.split(r"[^a-zA-Z0-9]+", text)
    words = [w for w in words if w]
    if not words:
        return
    
    result = words[0].lower() + "".join(w.capitalize() for w in words[1:])
    exec.insert(result)
