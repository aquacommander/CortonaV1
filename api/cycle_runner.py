from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from api.agent_mesh_runner import run_agent_mesh_event
from api.embeddings_runner import EmbeddingRunReport, rebuild_local_embeddings
from api.pipeline_runner import PipelineRunReport, run_pipeline_from_files
from api.state_runner import compute_user_state
from core.telemetry import JsonlMetricsLogger, run_timed
from storage.sqlite_store import SQLiteStore


@dataclass(frozen=True)
class CognitiveCycleReport:
    pipeline: PipelineRunReport
    state: Dict[str, Any]
    agent_outcomes_count: int
    agent_notes: List[str]
    embedding: Optional[EmbeddingRunReport] = None
    embedding_error: str = ""
    metrics_path: str = ""
    db_path: str = ""
    index_path: str = ""
    metadata_path: str = ""


def run_cognitive_cycle_from_files(
    *,
    notes_path: str,
    calendar_path: str,
    reminders_path: str,
    db_path: str = "data/cortona.db",
    index_path: str = "data/memory.faiss",
    metadata_path: str = "data/memory.meta.json",
    metrics_path: str = "data/metrics.jsonl",
    rebuild_embeddings: bool = True,
    embeddings_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    local_files_only: bool = False,
) -> CognitiveCycleReport:
    for file_path in (notes_path, calendar_path, reminders_path):
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Missing required export file: {file_path}")

    logger = JsonlMetricsLogger(metrics_path)

    pipeline_report = run_timed(
        logger,
        layer="pipeline",
        action="normalize_and_store",
        fn=lambda: run_pipeline_from_files(
            db_path=db_path,
            notes_path=notes_path,
            calendar_path=calendar_path,
            reminders_path=reminders_path,
        ),
    )

    embedding_report: Optional[EmbeddingRunReport] = None
    embedding_error = ""
    if rebuild_embeddings:
        try:
            embedding_report = run_timed(
                logger,
                layer="embeddings",
                action="rebuild_local_index",
                fn=lambda: rebuild_local_embeddings(
                    db_path=db_path,
                    index_path=index_path,
                    metadata_path=metadata_path,
                    model_name=embeddings_model_name,
                    local_files_only=local_files_only,
                ),
            )
        except RuntimeError as exc:
            embedding_error = str(exc)

    state_snapshot = run_timed(
        logger,
        layer="state",
        action="compute_user_state",
        fn=lambda: compute_user_state(db_path=db_path),
    )

    store = SQLiteStore(db_path)
    canonical_ids = [obj.canonical_id for obj in store.fetch_canonical_objects()]
    agent_outcomes = run_timed(
        logger,
        layer="agents",
        action="dispatch_mesh_event",
        fn=lambda: run_agent_mesh_event(
            db_path=db_path,
            index_path=index_path,
            metadata_path=metadata_path,
            event_type="RELATION_GRAPH_UPDATED",
            payload={"canonical_ids": canonical_ids[:20], "query": "follow up priorities"},
            model_name=embeddings_model_name,
            local_files_only=local_files_only,
            data_dir=str(Path(db_path).parent),
        ),
    )

    agent_notes: List[str] = []
    for outcome in agent_outcomes:
        agent_notes.extend([f"{outcome.agent_name}: {note}" for note in outcome.notes])

    return CognitiveCycleReport(
        pipeline=pipeline_report,
        state={
            "energy_level": state_snapshot.energy_level,
            "stress_probability": state_snapshot.stress_probability,
            "focus_index": state_snapshot.focus_index,
            "execution_velocity": state_snapshot.execution_velocity,
            "domain_context": state_snapshot.domain_context,
            "features": {
                "recent_object_count": state_snapshot.features.recent_object_count,
                "upcoming_24h_count": state_snapshot.features.upcoming_24h_count,
                "overdue_reminder_count": state_snapshot.features.overdue_reminder_count,
                "follow_up_relation_count": state_snapshot.features.follow_up_relation_count,
                "active_domain_count": state_snapshot.features.active_domain_count,
            },
        },
        embedding=embedding_report,
        embedding_error=embedding_error,
        agent_outcomes_count=len(agent_outcomes),
        agent_notes=agent_notes,
        metrics_path=metrics_path,
        db_path=db_path,
        index_path=index_path,
        metadata_path=metadata_path,
    )
