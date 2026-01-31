"""
{
  "name": "MD5 Hash",
  "slug": "md5_hash",
  "description": "Calculate MD5 hash of text",
  "tags": ["hash", "crypto", "md5"],
  "bias": 0.0
}
"""

import hashlib


def main(exec):
    result = hashlib.md5(exec.text.encode("utf-8")).hexdigest()
    exec.insert(result)
    exec.post_info("MD5 hash calculated")
