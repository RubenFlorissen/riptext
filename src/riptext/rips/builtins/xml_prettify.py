"""
{
  "name": "XML Prettify",
  "slug": "xml_prettify",
  "description": "Pretty-print XML",
  "tags": ["xml", "format"],
  "aliases": ["format xml"],
  "bias": 0.0,
  "category": "Data"
}
"""

from xml.dom import minidom


def transform(text: str) -> str:
    document = minidom.parseString(text.encode("utf-8"))
    return document.toprettyxml(indent="  ")
