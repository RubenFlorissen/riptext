"""
{
  "name": "Timestamp Convert",
  "slug": "timestamp_convert",
  "description": "Convert Unix timestamps to ISO UTC, or ISO datetimes to Unix seconds",
  "tags": ["timestamp", "date", "time"],
  "aliases": ["unix time", "epoch"],
  "bias": 0.0,
  "category": "Utility"
}
"""

from datetime import datetime, timezone


def transform(text: str) -> str:
    value = text.strip()
    if not value:
        return text

    try:
        timestamp = float(value)
    except ValueError:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        seconds = parsed.timestamp()
        return str(int(seconds) if seconds.is_integer() else seconds)

    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
