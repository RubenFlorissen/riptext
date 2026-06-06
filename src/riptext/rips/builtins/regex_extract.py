"""
{
  "name": "Regex Extract",
  "slug": "regex_extract",
  "description": "Use the first line as a regex and extract matches from the rest",
  "tags": ["regex", "extract", "text"],
  "aliases": ["grep", "match"],
  "bias": 0.0,
  "category": "Text"
}
"""

import re


def main(exec):
    pattern, separator, body = exec.text.partition("\n")
    if not separator or not pattern.strip():
        exec.post_error("First line must be the regex pattern")
        return

    matches = []
    for match in re.finditer(pattern, body, flags=re.MULTILINE):
        if match.groups():
            matches.append("\t".join(group or "" for group in match.groups()))
        else:
            matches.append(match.group(0))
    exec.insert("\n".join(matches))
    exec.post_info(f"Extracted {len(matches)} matches")
