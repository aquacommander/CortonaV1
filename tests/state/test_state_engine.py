from datetime import datetime, timezone

from core.canonical_schema import CanonicalObject
from state.engine import DeterministicStateEngine
from storage.sqlite_store import SQLiteStore


def test_state_engine_computes_expected_signals() -> None:
    now = datetime(2026, 2, 27, 18, 0, tzinfo=timezone.utc)
    objects = [
        CanonicalObject(
            canonical_id="co_1",
            source_system="apple_notes",
            source_record_type="note",
            title="Roadmap draft",
            content="Prepare milestones",
            created_at=datetime(2026, 2, 26, 9, 0, tzinfo=timezone.utc),
            people=["sam@example.com"],
            domain="work",
        ),
        CanonicalObject(
            canonical_id="co_2",
            source_system="google_calendar",
            source_record_type="event",
            title="Roadmap sync",
            content="Discuss dependencies",
            start_at=datetime(2026, 2, 27, 20, 0, tzinfo=timezone.utc),
            people=["sam@example.com"],
            domain="work",
        ),
        CanonicalObject(
            canonical_id="co_3",
            source_system="apple_reminders",
            source_record_type="reminder",
            title="Send recap",
            content="Email summary",
            due_at=datetime(2026, 2, 27, 12, 0, tzinfo=timezone.utc),
            people=["sam@example.com"],
            domain="work",
        ),
    ]
    relations = [
        {
            "relation_id": "r1",
            "from_canonical_id": "co_1",
            "to_canonical_id": "co_2",
            "relation_type": "FOLLOW_UP",
            "reason": "delta_hours=11.00",
            "confidence": 1.0,
            "created_at": "2026-02-27T00:00:00+00:00",
        }
    ]

    engine = DeterministicStateEngine()
    state = engine.calculate(objects, relations, now=now)

    assert 0.0 <= state.energy_level <= 100.0
    assert 0.0 <= state.focus_index <= 100.0
    assert 0.0 <= state.execution_velocity <= 100.0
    assert 0.0 <= state.stress_probability <= 1.0
    assert state.domain_context == "work"
    assert state.features.recent_object_count == 3
    assert state.features.follow_up_relation_count == 1
    assert state.features.overdue_reminder_count == 1
    assert state.features.upcoming_24h_count == 1


def test_state_engine_reads_from_store(tmp_path) -> None:
    db_path = tmp_path / "memory.db"
    store = SQLiteStore(str(db_path))
    store.initialize_schema()
    store.upsert_canonical_object(
        CanonicalObject(
            canonical_id="co_1",
            source_system="apple_notes",
            source_record_type="note",
            title="Prep brief",
            content="Draft narrative.",
            created_at=datetime(2026, 2, 27, 10, 0, tzinfo=timezone.utc),
            domain="strategy",
        )
    )
    store.replace_relations([])

    engine = DeterministicStateEngine()
    snapshot = engine.calculate_from_store(store, now=datetime(2026, 2, 27, 12, 0, tzinfo=timezone.utc))
    assert snapshot.features.recent_object_count == 1
    assert snapshot.domain_context == "strategy"
