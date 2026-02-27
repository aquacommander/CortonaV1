from datetime import datetime

from core.canonical_schema import CanonicalObject
from graph.relation_builder import (
    FOLLOW_UP,
    SAME_DAY,
    SAME_DOMAIN,
    SAME_PERSON,
    build_relations,
    rebuild_and_store_relations,
)
from storage.sqlite_store import SQLiteStore


def test_build_relations_generates_expected_types() -> None:
    obj_a = CanonicalObject(
        canonical_id="co_a",
        source_system="apple_notes",
        source_record_type="note",
        title="Discuss roadmap",
        content="Follow up with Sam.",
        created_at=datetime.fromisoformat("2026-02-26T09:00:00"),
        people=["sam@example.com"],
        domain="work",
    )
    obj_b = CanonicalObject(
        canonical_id="co_b",
        source_system="google_calendar",
        source_record_type="event",
        title="Roadmap sync",
        content="Product and engineering sync.",
        start_at=datetime.fromisoformat("2026-02-26T14:00:00"),
        people=["sam@example.com"],
        domain="work",
    )
    obj_c = CanonicalObject(
        canonical_id="co_c",
        source_system="apple_reminders",
        source_record_type="reminder",
        title="Send roadmap summary",
        content="Email summary and action items.",
        due_at=datetime.fromisoformat("2026-02-27T10:00:00"),
        people=["sam@example.com"],
        domain="work",
    )

    relations = build_relations([obj_a, obj_b, obj_c])
    relation_types = {relation.relation_type for relation in relations}

    assert SAME_DAY in relation_types
    assert SAME_PERSON in relation_types
    assert SAME_DOMAIN in relation_types
    assert FOLLOW_UP in relation_types


def test_rebuild_and_store_relations_writes_to_sqlite(tmp_path) -> None:
    db_path = tmp_path / "memory.db"
    store = SQLiteStore(str(db_path))
    store.initialize_schema()

    store.upsert_canonical_objects(
        [
            CanonicalObject(
                canonical_id="co_1",
                source_system="apple_notes",
                source_record_type="note",
                title="Prep 1:1",
                content="Agenda for teammate check-in.",
                created_at=datetime.fromisoformat("2026-02-20T09:00:00"),
                people=["lee@example.com"],
                domain="management",
            ),
            CanonicalObject(
                canonical_id="co_2",
                source_system="google_calendar",
                source_record_type="event",
                title="1:1 Meeting",
                content="Weekly check-in.",
                start_at=datetime.fromisoformat("2026-02-20T10:00:00"),
                people=["lee@example.com"],
                domain="management",
            ),
        ]
    )

    relation_count = rebuild_and_store_relations(store)
    persisted = store.fetch_relations()

    assert relation_count > 0
    assert len(persisted) == relation_count
