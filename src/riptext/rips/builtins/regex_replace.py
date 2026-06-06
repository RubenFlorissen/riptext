"""
{
  "name": "Regex Replace",
  "slug": "regex_replace",
  "description": "Use line 1 as regex, line 2 as replacement, and replace in the rest",
  "tags": ["regex", "replace", "text"],
  "aliases": ["substitute", "sub"],
  "bias": 0.0,
  "category": "Text"
}
"""

import re


def main(exec):
    lines = exec.text.split("\n", 2)
    if len(lines) < 3 or not lines[0].strip():
        exec.post_error("Use: pattern, replacement, then text on separate lines")
        return

    result, count = re.subn(lines[0], lines[1], lines[2], flags=re.MULTILINE)
    exec.insert(result)
    exec.post_info(f"Replaced {count} matches")
