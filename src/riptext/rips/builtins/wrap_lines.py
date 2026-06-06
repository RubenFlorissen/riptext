"""
{
  "name": "Wrap Lines (80)",
  "slug": "wrap_lines",
  "description": "Wrap text at 80 characters",
  "tags": ["wrap", "format", "lines"],
  "bias": 0.0,
  "category": "Lines"
}
"""

import textwrap


def main(exec):
    wrapped = textwrap.fill(exec.text, width=80)
    exec.insert(wrapped)
