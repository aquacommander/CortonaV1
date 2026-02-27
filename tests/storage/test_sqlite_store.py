from core.canonical_schema import CanonicalObject
from storage.sqlite_store import SQLiteStore


def test_initialize_schema_creates_tables(tmp_path) -> None:
    db_path = tmp_path / "memory.db"
    store = SQLiteStore(str(db_path))
    store.initialize_schema()

    with store._connect() as conn:
        names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'index')"
            ).fetchall()
        }

    assert "canonical_objects" in names
    assert "relations" in names
    assert "idx_canonical_objects_created_at" in names
    assert "idx_relations_created_at" in names


def test_upsert_and_fetch_canonical_objects(tmp_path) -> None:
    db_path = tmp_path / "memory.db"
    store = SQLiteStore(str(db_path))
    store.initialize_schema()

    obj = CanonicalObject(
        canonical_id="co_a",
        source_system="apple_notes",
        source_record_type="note",
        title="Plan",
        content="Ship milestone.",
        people=["alex@example.com"],
        labels=["work"],
        domain="work",
    )

    store.upsert_canonical_object(obj)
    fetched = store.fetch_canonical_objects()
    assert len(fetched) == 1
    assert fetched[0].canonical_id == "co_a"
    assert fetched[0].people == ["alex@example.com"]
