from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def load_json_file(path: str) -> Any:
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def as_records(payload: Any, *, preferred_keys: List[str]) -> List[Dict[str, Any]]:
    """Normalize common export payload shapes into a list of dict records."""
    if payload is None:
        return []
    if isinstance(payload, list):
        return [record for record in payload if isinstance(record, dict)]
    if isinstance(payload, dict):
        for key in preferred_keys:
            candidate = payload.get(key)
            if isinstance(candidate, list):
                return [record for record in candidate if isinstance(record, dict)]
        return [payload]
    raise TypeError(f"Unsupported JSON payload type: {type(payload)!r}")
