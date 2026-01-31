"""
{
  "name": "snake_case",
  "slug": "snake_case",
  "description": "Convert to snake_case",
  "tags": ["case", "snake", "format"],
  "bias": 0.0
}
"""

import re


def main(exec):
    text = exec.text.strip()
    # Insert underscore before uppercase letters
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", text)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    # Replace non-alphanumeric with underscore
    s3 = re.sub(r"[^a-zA-Z0-9]+", "_", s2)
    result = s3.lower().strip("_")
    exec.insert(result)
