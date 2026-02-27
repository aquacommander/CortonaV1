from __future__ import annotations

from typing import Any, Dict, Iterable, List

from core.canonical_schema import CanonicalObject
from core.deterministic_id import make_canonical_id
from ingestion.common import normalize_string_list, parse_datetime

SOURCE_SYSTEM = "google_calendar"
SOURCE_RECORD_TYPE = "event"


def _source_event_id(raw_event: Dict[str, Any]) -> str:
    return str(
        raw_event.get("id")
        or raw_event.get("event_id")
        or raw_event.get("iCalUID")
        or raw_event.get("summary")
        or raw_event.get("created")
        or "unknown_event"
    )


def _extract_event_time(raw_time: Any) -> Any:
    if isinstance(raw_time, dict):
        return raw_time.get("dateTime") or raw_time.get("date")
    return raw_time


def map_event(raw_event: Dict[str, Any]) -> CanonicalObject:
    source_id = _source_event_id(raw_event)
    title = str(raw_event.get("summary") or raw_event.get("title") or "").strip()
    content = str(raw_event.get("description") or raw_event.get("content") or "").strip()
    people = normalize_string_list(
        [
            attendee.get("email")
            for attendee in (raw_event.get("attendees") or [])
            if isinstance(attendee, dict)
        ]
    )
    labels = normalize_string_list(raw_event.get("labels") or [])
    domain = str(raw_event.get("calendar") or raw_event.get("domain") or "calendar").strip() or "calendar"

    return CanonicalObject(
        canonical_id=make_canonical_id(SOURCE_SYSTEM, SOURCE_RECORD_TYPE, source_id),
        source_system=SOURCE_SYSTEM,
        source_record_type=SOURCE_RECORD_TYPE,
        title=title,
        content=content,
        start_at=parse_datetime(_extract_event_time(raw_event.get("start"))),
        end_at=parse_datetime(_extract_event_time(raw_event.get("end"))),
        created_at=parse_datetime(raw_event.get("created")),
        updated_at=parse_datetime(raw_event.get("updated")),
        people=people,
        labels=labels,
        domain=domain,
    )


def map_events(raw_export: Iterable[Dict[str, Any]]) -> List[CanonicalObject]:
    return [map_event(raw_event) for raw_event in raw_export]
