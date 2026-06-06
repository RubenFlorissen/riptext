"""
{
  "name": "Detect Language",
  "slug": "detect_language",
  "description": "Auto-detect and apply syntax highlighting",
  "tags": ["syntax", "language", "highlight"],
  "bias": 0.0,
  "category": "Utility"
}
"""


def main(exec):
    # This is a special script that signals the app to detect language
    # The actual detection happens in the app
    exec.post_info("detect_language")
