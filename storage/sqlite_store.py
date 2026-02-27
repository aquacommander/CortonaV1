from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from core.canonical_schema import CanonicalObject


def _to_iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt is not None else None


class SQLiteStore:
    """Local SQLite persistence for canonical objects and graph relations."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS canonical_objects (
                    canonical_id TEXT PRIMARY KEY,
                    source_system TEXT NOT NULL,
                    source_record_type TEXT NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    content TEXT NOT NULL DEFAULT '',
                    start_at TEXT,
                    end_at TEXT,
                    due_at TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    people_json TEXT NOT NULL,
                    labels_json TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    ingested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS relations (
                    relation_id TEXT PRIMARY KEY,
                    from_canonical_id TEXT NOT NULL,
                    to_canonical_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    reason TEXT NOT NULL DEFAULT '',
                    confidence REAL NOT NULL DEFAULT 1.0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(from_canonical_id) REFERENCES canonical_objects(canonical_id) ON DELETE CASCADE,
                    FOREIGN KEY(to_canonical_id) REFERENCES canonical_objects(canonical_id) ON DELETE CASCADE,
                    UNIQUE(from_canonical_id, to_canonical_id, relation_type)
                );

                CREATE INDEX IF NOT EXISTS idx_canonical_objects_start_at
                    ON canonical_objects(start_at);
                CREATE INDEX IF NOT EXISTS idx_canonical_objects_due_at
                    ON canonical_objects(due_at);
                CREATE INDEX IF NOT EXISTS idx_canonical_objects_created_at
                    ON canonical_objects(created_at);
                CREATE INDEX IF NOT EXISTS idx_canonical_objects_updated_at
                    ON canonical_objects(updated_at);
                CREATE INDEX IF NOT EXISTS idx_relations_created_at
                    ON relations(created_at);
                CREATE INDEX IF NOT EXISTS idx_relations_type
                    ON relations(relation_type);
                """
            )

    def upsert_canonical_object(self, obj: CanonicalObject) -> None:
        self.upsert_canonical_objects([obj])

    def upsert_canonical_objects(self, objects: Sequence[CanonicalObject]) -> None:
        if not objects:
            return

        rows = [
            (
                obj.canonical_id,
                obj.source_system,
                obj.source_record_type,
                obj.title,
                obj.content,
                _to_iso(obj.start_at),
                _to_iso(obj.end_at),
                _to_iso(obj.due_at),
                _to_iso(obj.created_at),
                _to_iso(obj.updated_at),
                json.dumps(obj.people, ensure_ascii=True, separators=(",", ":")),
                json.dumps(obj.labels, ensure_ascii=True, separators=(",", ":")),
                obj.domain,
            )
            for obj in objects
        ]

        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO canonical_objects (
                    canonical_id,
                    source_system,
                    source_record_type,
                    title,
                    content,
                    start_at,
                    end_at,
                    due_at,
                    created_at,
                    updated_at,
                    people_json,
                    labels_json,
                    domain
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(canonical_id) DO UPDATE SET
                    source_system = excluded.source_system,
                    source_record_type = excluded.source_record_type,
                    title = excluded.title,
                    content = excluded.content,
                    start_at = excluded.start_at,
                    end_at = excluded.end_at,
                    due_at = excluded.due_at,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at,
                    people_json = excluded.people_json,
                    labels_json = excluded.labels_json,
                    domain = excluded.domain
                """,
                rows,
            )

    def fetch_canonical_objects(self) -> List[CanonicalObject]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    canonical_id,
                    source_system,
                    source_record_type,
                    title,
                    content,
                    start_at,
                    end_at,
                    due_at,
                    created_at,
                    updated_at,
                    people_json,
                    labels_json,
                    domain
                FROM canonical_objects
                """
            ).fetchall()

        return [
            CanonicalObject(
                canonical_id=row["canonical_id"],
                source_system=row["source_system"],
                source_record_type=row["source_record_type"],
                title=row["title"],
                content=row["content"],
                start_at=row["start_at"],
                end_at=row["end_at"],
                due_at=row["due_at"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                people=json.loads(row["people_json"]),
                labels=json.loads(row["labels_json"]),
                domain=row["domain"],
            )
            for row in rows
        ]

    def replace_relations(self, relations: Iterable[Dict[str, Any]]) -> None:
        relation_rows = [
            (
                relation["relation_id"],
                relation["from_canonical_id"],
                relation["to_canonical_id"],
                relation["relation_type"],
                relation.get("reason", ""),
                float(relation.get("confidence", 1.0)),
            )
            for relation in relations
        ]

        with self._connect() as conn:
            conn.execute("DELETE FROM relations")
            if relation_rows:
                conn.executemany(
                    """
                    INSERT INTO relations (
                        relation_id,
                        from_canonical_id,
                        to_canonical_id,
                        relation_type,
                        reason,
                        confidence
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(from_canonical_id, to_canonical_id, relation_type) DO UPDATE SET
                        relation_id = excluded.relation_id,
                        reason = excluded.reason,
                        confidence = excluded.confidence
                    """,
                    relation_rows,
                )

    def fetch_relations(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    relation_id,
                    from_canonical_id,
                    to_canonical_id,
                    relation_type,
                    reason,
                    confidence,
                    created_at
                FROM relations
                ORDER BY from_canonical_id, to_canonical_id, relation_type
                """
            ).fetchall()
        return [dict(row) for row in rows]
