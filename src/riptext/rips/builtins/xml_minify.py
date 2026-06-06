"""
{
  "name": "XML Minify",
  "slug": "xml_minify",
  "description": "Remove insignificant XML whitespace",
  "tags": ["xml", "minify"],
  "aliases": ["compact xml"],
  "bias": 0.0,
  "category": "Data"
}
"""

from xml.etree import ElementTree


def transform(text: str) -> str:
    root = ElementTree.fromstring(text)
    return ElementTree.tostring(root, encoding="unicode")
