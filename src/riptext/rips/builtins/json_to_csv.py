"""
{
  "name": "JSON to CSV",
  "slug": "json_to_csv",
  "description": "Convert JSON array to CSV",
  "tags": ["csv", "json", "convert"],
  "bias": 0.0,
  "category": "Data"
}
"""

import csv
import io
import json


def main(exec):
    try:
        data = json.loads(exec.text)
        if not isinstance(data, list) or not data:
            exec.post_error("Expected non-empty JSON array")
            return
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        exec.insert(output.getvalue())
        exec.post_info(f"Converted {len(data)} rows")
    except json.JSONDecodeError as e:
        exec.post_error(f"Invalid JSON: {e}")
    except Exception as e:
        exec.post_error(f"Conversion error: {e}")
