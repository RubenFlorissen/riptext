"""
{
  "name": "kebab-case",
  "slug": "kebab_case",
  "description": "Convert to kebab-case",
  "tags": ["case", "kebab", "format"],
  "bias": 0.0,
  "category": "Text Case"
}
"""

import re


def main(exec):
    text = exec.text.strip()
    # Insert hyphen before uppercase letters
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", text)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s1)
    # Replace non-alphanumeric with hyphen
    s3 = re.sub(r"[^a-zA-Z0-9]+", "-", s2)
    result = s3.lower().strip("-")
    exec.insert(result)
