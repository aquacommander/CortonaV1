from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence

from core.canonical_schema import CanonicalObject
from graph.relation_builder import rebuild_and_store_relations
from ingestion.calendar_mapper import map_events
from ingestion.export_loader import as_records, load_json_file
from ingestion.notes_mapper import map_notes
from ingestion.reminders_mapper import map_reminders
from storage.sqlite_store import SQLiteStore


@dataclass(frozen=True)
class PipelineRunReport:
    notes_count: int
    calendar_count: int
    reminders_count: int
    canonical_count: int
    relation_count: int
    db_path: str


class DeterministicNormalizationPipeline:
    """Deterministic ingestion + storage + relation build orchestrator."""

    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def run(
        self,
        *,
        notes_payload: Any,
        calendar_payload: Any,
        reminders_payload: Any,
    ) -> PipelineRunReport:
        self.store.initialize_schema()

        note_records = as_records(notes_payload, preferred_keys=["notes", "items", "data"])
        calendar_records = as_records(calendar_payload, preferred_keys=["events", "items", "data"])
        reminder_records = as_records(reminders_payload, preferred_keys=["reminders", "items", "data"])

        mapped_notes = map_notes(note_records)
        mapped_events = map_events(calendar_records)
        mapped_reminders = map_reminders(reminder_records)

        canonical_objects = self._dedupe_canonical_objects(
            [*mapped_notes, *mapped_events, *mapped_reminders]
        )
        self.store.upsert_canonical_objects(canonical_objects)
        relation_count = rebuild_and_store_relations(self.store, canonical_objects)

        return PipelineRunReport(
            notes_count=len(mapped_notes),
            calendar_count=len(mapped_events),
            reminders_count=len(mapped_reminders),
            canonical_count=len(canonical_objects),
            relation_count=relation_count,
            db_path=self.store.db_path,
        )

    @staticmethod
    def _dedupe_canonical_objects(objects: Sequence[CanonicalObject]) -> List[CanonicalObject]:
        # Deterministic last-write-wins by stable iteration order.
        dedup: Dict[str, CanonicalObject] = {}
        for obj in objects:
            dedup[obj.canonical_id] = obj
        return list(dedup.values())


def run_pipeline_from_files(
    *,
    db_path: str,
    notes_path: str,
    calendar_path: str,
    reminders_path: str,
) -> PipelineRunReport:
    for path in (notes_path, calendar_path, reminders_path):
        if not Path(path).exists():
            raise FileNotFoundError(f"Export file not found: {path}")

    store = SQLiteStore(db_path)
    pipeline = DeterministicNormalizationPipeline(store)
    return pipeline.run(
        notes_payload=load_json_file(notes_path),
        calendar_payload=load_json_file(calendar_path),
        reminders_payload=load_json_file(reminders_path),
    )
