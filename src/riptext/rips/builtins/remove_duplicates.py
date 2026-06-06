"""
{
  "name": "Remove Duplicate Lines",
  "slug": "remove_duplicates",
  "description": "Remove duplicate lines, keeping first occurrence",
  "tags": ["text", "lines", "duplicates"],
  "bias": 0.0,
  "category": "Lines"
}
"""


def transform(text: str) -> str:
    seen: set[str] = set()
    result: list[str] = []
    for line in text.split("\n"):
        if line not in seen:
            seen.add(line)
            result.append(line)
    return "\n".join(result)
