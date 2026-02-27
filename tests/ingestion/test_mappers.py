from ingestion.calendar_mapper import map_event
from ingestion.notes_mapper import map_note
from ingestion.reminders_mapper import map_reminder


def test_note_mapping_is_deterministic() -> None:
    raw_note = {
        "id": "note-123",
        "title": "Weekly Review",
        "content": "Summarize wins and blockers.",
        "created_at": "2026-02-20T10:00:00Z",
        "updated_at": "2026-02-20T11:00:00Z",
        "tags": ["review", "work"],
        "people": ["alex@example.com"],
        "folder": "work",
    }
    first = map_note(raw_note)
    second = map_note(raw_note)
    assert first.canonical_id == second.canonical_id
    assert first.domain == "work"


def test_calendar_event_mapping_fields() -> None:
    raw_event = {
        "id": "evt-456",
        "summary": "Product Sync",
        "description": "Weekly product status sync.",
        "start": {"dateTime": "2026-02-21T15:00:00Z"},
        "end": {"dateTime": "2026-02-21T15:30:00Z"},
        "attendees": [{"email": "sam@example.com"}, {"email": "lee@example.com"}],
        "calendar": "work",
    }
    event = map_event(raw_event)
    assert event.source_record_type == "event"
    assert event.title == "Product Sync"
    assert event.people == ["sam@example.com", "lee@example.com"]


def test_reminder_mapping_due_date() -> None:
    raw_reminder = {
        "id": "rem-789",
        "title": "Submit expense report",
        "notes": "Before Friday EOD",
        "dueDate": "2026-02-27T17:00:00Z",
        "list": "admin",
    }
    reminder = map_reminder(raw_reminder)
    assert reminder.source_record_type == "reminder"
    assert reminder.due_at is not None
    assert reminder.domain == "admin"
