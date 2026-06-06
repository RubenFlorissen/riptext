"""
{
  "name": "JWT Decode",
  "slug": "jwt_decode",
  "description": "Decode JWT header and payload without verifying signature",
  "tags": ["jwt", "json", "decode"],
  "aliases": ["token"],
  "bias": 0.0,
  "category": "Data"
}
"""

import base64
import json


def _decode_part(part: str) -> dict:
    padded = part + "=" * (-len(part) % 4)
    decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
    return json.loads(decoded.decode("utf-8"))


def main(exec):
    parts = exec.text.strip().split(".")
    if len(parts) < 2:
        exec.post_error("JWT must have at least header and payload parts")
        return
    header = _decode_part(parts[0])
    payload = _decode_part(parts[1])
    exec.insert(json.dumps({"header": header, "payload": payload}, indent=2))
    exec.post_info("Decoded JWT without verifying signature")
