"""
{
  "name": "Count Stats",
  "slug": "count_stats",
  "description": "Count characters, words, and lines",
  "tags": ["count", "words", "lines", "stats"],
  "bias": 0.0,
  "category": "Analysis"
}
"""


def main(exec):
    text = exec.text
    chars = len(text)
    words = len(text.split())
    lines = text.count("\n") + (1 if text else 0)
    
    result = f"Characters: {chars}\nWords: {words}\nLines: {lines}"
    exec.insert(result)
