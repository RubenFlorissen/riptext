"""
{
  "name": "YAML to JSON",
  "slug": "yaml_to_json",
  "description": "Convert YAML to pretty-printed JSON",
  "tags": ["yaml", "json", "convert"],
  "aliases": ["yml to json"],
  "bias": 0.0,
  "category": "Data"
}
"""

import json

import yaml


def main(exec):
    try:
        data = yaml.safe_load(exec.text)
        exec.insert(json.dumps(data, indent=2, sort_keys=True))
        exec.post_info("Converted YAML to JSON")
    except yaml.YAMLError as exc:
        exec.post_error(f"Invalid YAML: {exc}")
    except TypeError as exc:
        exec.post_error(f"Conversion error: {exc}")
