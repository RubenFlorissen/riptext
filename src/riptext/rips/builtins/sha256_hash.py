"""
{
  "name": "SHA256 Hash",
  "slug": "sha256_hash",
  "description": "Calculate SHA256 hash of text",
  "tags": ["hash", "crypto", "sha256"],
  "bias": 0.0
}
"""

import hashlib


def main(exec):
    result = hashlib.sha256(exec.text.encode("utf-8")).hexdigest()
    exec.insert(result)
    exec.post_info("SHA256 hash calculated")
