from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from agents.builtin_agents import FollowUpPlannerAgent, MemoryContextAgent
from agents.contracts import AgentEvent, AgentOutcome, VectorMemoryProvider
from agents.mesh import AgentMesh
from agents.providers import (
    EmbeddingVectorMemoryProvider,
    NullVectorMemoryProvider,
    SQLiteGraphMemoryProvider,
    StoreBackedStateProvider,
)
from embeddings.faiss_store import LocalFaissStore
from embeddings.indexer import EmbeddingIndexer
from embeddings.models import SentenceTransformerEmbeddingModel
from state.engine import DeterministicStateEngine
from storage.sqlite_store import SQLiteStore
from tools.builtin_tools import build_local_tool_registry


def run_agent_mesh_event(
    *,
    db_path: str,
    index_path: str,
    metadata_path: str,
    event_type: str,
    payload: Dict[str, Any],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    local_files_only: bool = False,
    data_dir: str = "data",
) -> List[AgentOutcome]:
    store = SQLiteStore(db_path)
    state_engine = DeterministicStateEngine()
    tool_registry = build_local_tool_registry(data_dir)

    vector_memory: VectorMemoryProvider = NullVectorMemoryProvider()
    index_exists = Path(index_path).exists() and Path(metadata_path).exists()
    if index_exists:
        try:
            model = SentenceTransformerEmbeddingModel(model_name=model_name, local_files_only=local_files_only)
            vector_store = LocalFaissStore(index_path=index_path, metadata_path=metadata_path)
            embedding_indexer = EmbeddingIndexer(model=model, vector_store=vector_store)
            vector_memory = EmbeddingVectorMemoryProvider(embedding_indexer)
        except RuntimeError:
            vector_memory = NullVectorMemoryProvider()

    mesh = AgentMesh(
        agents=[FollowUpPlannerAgent(), MemoryContextAgent()],
        graph_memory=SQLiteGraphMemoryProvider(store),
        vector_memory=vector_memory,
        state_provider=StoreBackedStateProvider(store, state_engine),
        tool_registry=tool_registry,
    )
    event = AgentEvent(event_type=event_type, emitted_at=datetime.now(timezone.utc), payload=payload)
    return mesh.dispatch(event)
