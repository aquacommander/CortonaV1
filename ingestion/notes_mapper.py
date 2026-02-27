from __future__ import annotations

from typing import Any, Dict, Iterable, List

from core.canonical_schema import CanonicalObject
from core.deterministic_id import make_canonical_id
from ingestion.common import normalize_string_list, parse_datetime

SOURCE_SYSTEM = "apple_notes"
SOURCE_RECORD_TYPE = "note"


def _source_note_id(raw_note: Dict[str, Any]) -> str:
    return str(
        raw_note.get("id")
        or raw_note.get("note_id")
        or raw_note.get("identifier")
        or raw_note.get("uuid")
        or raw_note.get("title")
        or raw_note.get("created")
        or "unknown_note"
    )


def map_note(raw_note: Dict[str, Any]) -> CanonicalObject:
    source_id = _source_note_id(raw_note)
    title = str(raw_note.get("title") or raw_note.get("name") or "").strip()
    content = str(raw_note.get("content") or raw_note.get("body") or "").strip()
    labels = normalize_string_list(raw_note.get("tags") or raw_note.get("labels") or [])
    people = normalize_string_list(raw_note.get("participants") or raw_note.get("people") or [])
    domain = str(raw_note.get("folder") or raw_note.get("domain") or "notes").strip() or "notes"

    return CanonicalObject(
        canonical_id=make_canonical_id(SOURCE_SYSTEM, SOURCE_RECORD_TYPE, source_id),
        source_system=SOURCE_SYSTEM,
        source_record_type=SOURCE_RECORD_TYPE,
        title=title,
        content=content,
        created_at=parse_datetime(raw_note.get("created_at") or raw_note.get("created")),
        updated_at=parse_datetime(raw_note.get("updated_at") or raw_note.get("updated")),
        people=people,
        labels=labels,
        domain=domain,
    )


def map_notes(raw_export: Iterable[Dict[str, Any]]) -> List[CanonicalObject]:
    return [map_note(raw_note) for raw_note in raw_export]
