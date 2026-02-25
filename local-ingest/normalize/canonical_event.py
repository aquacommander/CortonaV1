"""Canonical schema and deterministic normalization logic.

This module intentionally avoids inference. It maps known fields from raw
source payloads into a single schema and preserves original records in
`raw_record` for traceability.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CanonicalEvent:
    """Canonical representation for notes, tasks, and events."""

    canonical_id: str
    source_system: str
    source_record_type: str
    source_record_id: str | None
    title: str | None
    content: str | None
    start_at: str | None
    end_at: str | None
    due_at: str | None
    created_at: str | None
    updated_at: str | None
    status: str | None
    location: str | None
    labels: list[str] = field(default_factory=list)
    participants: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
    raw_record: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable canonical record."""
        return asdict(self)


def _pick_string(record: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        value = record.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            return value
        return str(value)
    return None


def _pick_list_of_strings(record: dict[str, Any], keys: list[str]) -> list[str]:
    for key in keys:
        value = record.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]
    return []


def _records_from_payload(payload: Any, list_key: str) -> list[dict[str, Any]]:
    """Extract list of dict records from known payload shapes."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if isinstance(payload, dict):
        node = payload.get(list_key)
        if isinstance(node, list):
            return [item for item in node if isinstance(item, dict)]

    return []


def _normalize_apple_notes(payload: Any) -> list[CanonicalEvent]:
    records = _records_from_payload(payload, list_key="notes")
    normalized: list[CanonicalEvent] = []

    for index, record in enumerate(records):
        source_id = _pick_string(record, ["id", "note_id", "uuid"])
        normalized.append(
            CanonicalEvent(
                canonical_id=f"apple_notes:{source_id or index}",
                source_system="apple_notes",
                source_record_type="note",
                source_record_id=source_id,
                title=_pick_string(record, ["title", "name"]),
                content=_pick_string(record, ["body", "content", "text"]),
                start_at=None,
                end_at=None,
                due_at=None,
                created_at=_pick_string(record, ["created_at", "creationDate"]),
                updated_at=_pick_string(record, ["updated_at", "modificationDate"]),
                status=_pick_string(record, ["status"]),
                location=None,
                labels=_pick_list_of_strings(record, ["tags", "labels"]),
                participants=[],
                extra={"folder": _pick_string(record, ["folder", "account"])},
                raw_record=record,
            )
        )

    return normalized


def _normalize_apple_reminders(payload: Any) -> list[CanonicalEvent]:
    records = _records_from_payload(payload, list_key="reminders")
    normalized: list[CanonicalEvent] = []

    for index, record in enumerate(records):
        source_id = _pick_string(record, ["id", "reminder_id", "uuid"])
        completed = _pick_string(record, ["completed", "isCompleted"])
        status = "completed" if completed in {"true", "True", "1"} else "open"

        normalized.append(
            CanonicalEvent(
                canonical_id=f"apple_reminders:{source_id or index}",
                source_system="apple_reminders",
                source_record_type="task",
                source_record_id=source_id,
                title=_pick_string(record, ["title", "name"]),
                content=_pick_string(record, ["notes", "description"]),
                start_at=_pick_string(record, ["startDate"]),
                end_at=_pick_string(record, ["completionDate"]),
                due_at=_pick_string(record, ["dueDate", "due_at"]),
                created_at=_pick_string(record, ["creationDate", "created_at"]),
                updated_at=_pick_string(record, ["modificationDate", "updated_at"]),
                status=_pick_string(record, ["status"]) or status,
                location=_pick_string(record, ["location"]),
                labels=_pick_list_of_strings(record, ["tags", "labels"]),
                participants=[],
                extra={"list": _pick_string(record, ["list", "calendar"])},
                raw_record=record,
            )
        )

    return normalized


def _normalize_google_calendar(payload: Any) -> list[CanonicalEvent]:
    records = _records_from_payload(payload, list_key="events")
    normalized: list[CanonicalEvent] = []

    for index, record in enumerate(records):
        source_id = _pick_string(record, ["id", "event_id"])
        attendees = record.get("attendees")
        participants: list[str] = []
        if isinstance(attendees, list):
            for attendee in attendees:
                if isinstance(attendee, dict):
                    participant = _pick_string(attendee, ["email", "displayName"])
                    if participant is not None:
                        participants.append(participant)
                elif attendee is not None:
                    participants.append(str(attendee))

        normalized.append(
            CanonicalEvent(
                canonical_id=f"google_calendar:{source_id or index}",
                source_system="google_calendar",
                source_record_type="event",
                source_record_id=source_id,
                title=_pick_string(record, ["summary", "title"]),
                content=_pick_string(record, ["description"]),
                start_at=_pick_string(record, ["start", "start_at"]),
                end_at=_pick_string(record, ["end", "end_at"]),
                due_at=None,
                created_at=_pick_string(record, ["created"]),
                updated_at=_pick_string(record, ["updated"]),
                status=_pick_string(record, ["status"]),
                location=_pick_string(record, ["location"]),
                labels=_pick_list_of_strings(record, ["tags", "labels"]),
                participants=participants,
                extra={"calendar_id": _pick_string(record, ["calendar_id"])},
                raw_record=record,
            )
        )

    return normalized


def normalize_raw_document(raw_document: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize a raw ingestion document into canonical records."""
    source = raw_document.get("source")
    payload = raw_document.get("payload")

    if source == "apple_notes":
        records = _normalize_apple_notes(payload)
    elif source == "apple_reminders":
        records = _normalize_apple_reminders(payload)
    elif source == "google_calendar":
        records = _normalize_google_calendar(payload)
    else:
        raise ValueError(f"Unsupported source: {source}")

    return [record.to_dict() for record in records]


def normalize_raw_file(raw_file_path: Path, normalized_output_dir: Path) -> Path:
    """Normalize one raw snapshot file and write canonical output."""
    normalized_output_dir.mkdir(parents=True, exist_ok=True)

    with raw_file_path.open("r", encoding="utf-8") as handle:
        raw_document = json.load(handle)

    source = str(raw_document.get("source", "unknown"))
    records = normalize_raw_document(raw_document)

    output_file = normalized_output_dir / f"{source}_canonical.json"
    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2, ensure_ascii=False)

    return output_file
