from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, List, Optional


def parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, (int, float)):
        # Handle epoch seconds and milliseconds.
        if value > 10_000_000_000:
            value = value / 1000.0
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        normalized = candidate.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            return None
    return None


def normalize_string_list(values: Iterable[Any]) -> List[str]:
    normalized: List[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            normalized.append(text)
    return normalized
