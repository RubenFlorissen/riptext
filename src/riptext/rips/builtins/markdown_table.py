"""
{
  "name": "Markdown Table",
  "slug": "markdown_table",
  "description": "Convert CSV/TSV to Markdown table",
  "tags": ["markdown", "table", "csv", "format"],
  "bias": 0.0,
  "category": "Formatting"
}
"""

import csv
import io


def main(exec):
    text = exec.text.strip()
    if not text:
        exec.post_error("No input")
        return
    
    # Auto-detect delimiter
    delimiter = "\t" if "\t" in text else ","
    
    try:
        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        rows = list(reader)
        if not rows:
            exec.post_error("No data found")
            return
        
        # Calculate column widths
        col_widths = [max(len(str(cell)) for cell in col) for col in zip(*rows)]
        
        lines = []
        for i, row in enumerate(rows):
            padded = [str(cell).ljust(col_widths[j]) for j, cell in enumerate(row)]
            lines.append("| " + " | ".join(padded) + " |")
            if i == 0:
                # Add separator after header
                sep = ["-" * w for w in col_widths]
                lines.append("| " + " | ".join(sep) + " |")
        
        exec.insert("\n".join(lines))
    except Exception as e:
        exec.post_error(f"Parse error: {e}")
