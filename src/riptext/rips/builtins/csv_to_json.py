"""
{
  "name": "CSV to JSON",
  "slug": "csv_to_json",
  "description": "Convert CSV to JSON array",
  "tags": ["csv", "json", "convert"],
  "bias": 0.0
}
"""

import csv
import io
import json


def main(exec):
    try:
        reader = csv.DictReader(io.StringIO(exec.text))
        rows = list(reader)
        exec.insert(json.dumps(rows, indent=2))
        exec.post_info(f"Converted {len(rows)} rows")
    except Exception as e:
        exec.post_error(f"CSV parse error: {e}")
