"""
{
  "name": "Title Case",
  "slug": "title_case",
  "description": "Convert to Title Case",
  "tags": ["case", "title", "format"],
  "bias": 0.0,
  "category": "Text Case"
}
"""


def main(exec):
    exec.insert(exec.text.title())
