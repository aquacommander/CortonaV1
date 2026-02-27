from __future__ import annotations

from typing import Any, Dict, Iterable, List

from core.canonical_schema import CanonicalObject
from core.deterministic_id import make_canonical_id
from ingestion.common import normalize_string_list, parse_datetime

SOURCE_SYSTEM = "apple_reminders"
SOURCE_RECORD_TYPE = "reminder"


def _source_reminder_id(raw_reminder: Dict[str, Any]) -> str:
    return str(
        raw_reminder.get("id")
        or raw_reminder.get("reminder_id")
        or raw_reminder.get("identifier")
        or raw_reminder.get("uuid")
        or raw_reminder.get("title")
        or raw_reminder.get("createdDate")
        or "unknown_reminder"
    )


def map_reminder(raw_reminder: Dict[str, Any]) -> CanonicalObject:
    source_id = _source_reminder_id(raw_reminder)
    title = str(raw_reminder.get("title") or raw_reminder.get("name") or "").strip()
    content = str(raw_reminder.get("notes") or raw_reminder.get("content") or "").strip()
    labels = normalize_string_list(raw_reminder.get("tags") or raw_reminder.get("labels") or [])
    people = normalize_string_list(raw_reminder.get("assignees") or raw_reminder.get("people") or [])
    domain = str(raw_reminder.get("list") or raw_reminder.get("domain") or "tasks").strip() or "tasks"

    return CanonicalObject(
        canonical_id=make_canonical_id(SOURCE_SYSTEM, SOURCE_RECORD_TYPE, source_id),
        source_system=SOURCE_SYSTEM,
        source_record_type=SOURCE_RECORD_TYPE,
        title=title,
        content=content,
        due_at=parse_datetime(raw_reminder.get("dueDate") or raw_reminder.get("due_at")),
        created_at=parse_datetime(raw_reminder.get("createdDate") or raw_reminder.get("created_at")),
        updated_at=parse_datetime(raw_reminder.get("modifiedDate") or raw_reminder.get("updated_at")),
        people=people,
        labels=labels,
        domain=domain,
    )


def map_reminders(raw_export: Iterable[Dict[str, Any]]) -> List[CanonicalObject]:
    return [map_reminder(raw_reminder) for raw_reminder in raw_export]
