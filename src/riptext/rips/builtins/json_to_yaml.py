"""
{
  "name": "JSON to YAML",
  "slug": "json_to_yaml",
  "description": "Convert JSON to YAML",
  "tags": ["json", "yaml", "convert"],
  "aliases": ["json to yml"],
  "bias": 0.0,
  "category": "Data"
}
"""

import json

import yaml


def main(exec):
    try:
        data = json.loads(exec.text)
        exec.insert(
            yaml.safe_dump(
                data,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
        )
        exec.post_info("Converted JSON to YAML")
    except json.JSONDecodeError as exc:
        exec.post_error(f"Invalid JSON: {exc}")
    except yaml.YAMLError as exc:
        exec.post_error(f"Conversion error: {exc}")
