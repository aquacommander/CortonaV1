from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


def _stable_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def make_canonical_id(source_system: str, source_record_type: str, source_record_id: str) -> str:
    """Generate deterministic canonical IDs from stable source identifiers."""
    stable_payload = {
        "source_system": source_system,
        "source_record_type": source_record_type,
        "source_record_id": source_record_id,
    }
    digest = hashlib.sha256(_stable_json(stable_payload).encode("utf-8")).hexdigest()
    return f"co_{digest[:24]}"
