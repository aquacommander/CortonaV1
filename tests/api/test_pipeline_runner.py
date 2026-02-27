from api.pipeline_runner import DeterministicNormalizationPipeline
from ingestion.common import parse_datetime
from storage.sqlite_store import SQLiteStore


def test_parse_datetime_is_utc_stable_for_epoch() -> None:
    parsed = parse_datetime(1_706_000_000)
    assert parsed is not None
    assert parsed.tzinfo is not None
    assert parsed.isoformat().endswith("+00:00")


def test_pipeline_runs_end_to_end_and_persists(tmp_path) -> None:
    db_path = tmp_path / "memory.db"
    store = SQLiteStore(str(db_path))
    pipeline = DeterministicNormalizationPipeline(store)

    notes_payload = {
        "notes": [
            {
                "id": "n-1",
                "title": "Roadmap Notes",
                "content": "Need follow-up with sam@example.com",
                "created_at": "2026-02-27T09:00:00Z",
                "people": ["sam@example.com"],
                "folder": "work",
            }
        ]
    }
    calendar_payload = {
        "events": [
            {
                "id": "e-1",
                "summary": "Roadmap Follow-up",
                "description": "Discuss priority changes.",
                "start": {"dateTime": "2026-02-27T11:00:00Z"},
                "end": {"dateTime": "2026-02-27T11:30:00Z"},
                "attendees": [{"email": "sam@example.com"}],
                "calendar": "work",
            }
        ]
    }
    reminders_payload = {
        "reminders": [
            {
                "id": "r-1",
                "title": "Send recap",
                "notes": "Share decision summary",
                "dueDate": "2026-02-28T10:00:00Z",
                "assignees": ["sam@example.com"],
                "list": "work",
            }
        ]
    }

    report = pipeline.run(
        notes_payload=notes_payload,
        calendar_payload=calendar_payload,
        reminders_payload=reminders_payload,
    )

    assert report.notes_count == 1
    assert report.calendar_count == 1
    assert report.reminders_count == 1
    assert report.canonical_count == 3
    assert report.relation_count > 0

    stored_objects = store.fetch_canonical_objects()
    stored_relations = store.fetch_relations()
    assert len(stored_objects) == 3
    assert len(stored_relations) == report.relation_count
