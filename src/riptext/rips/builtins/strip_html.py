"""
{
  "name": "Strip HTML",
  "slug": "strip_html",
  "description": "Remove HTML tags and keep text content",
  "tags": ["html", "strip", "text"],
  "aliases": ["plain text"],
  "bias": 0.0,
  "category": "Text"
}
"""

from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return "".join(self.parts)


def transform(text: str) -> str:
    parser = _TextExtractor()
    parser.feed(text)
    return parser.text()
