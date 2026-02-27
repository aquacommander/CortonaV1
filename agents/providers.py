from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from embeddings.indexer import EmbeddingIndexer
from state.engine import DeterministicStateEngine
from state.models import UserStateSnapshot
from storage.sqlite_store import SQLiteStore


class SQLiteGraphMemoryProvider:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def get_relations(self, canonical_ids: Sequence[str]) -> List[Dict[str, object]]:
        relations = self.store.fetch_relations()
        if not canonical_ids:
            return relations
        wanted = {canonical_id for canonical_id in canonical_ids}
        return [
            relation
            for relation in relations
            if str(relation.get("from_canonical_id")) in wanted
            or str(relation.get("to_canonical_id")) in wanted
        ]


class EmbeddingVectorMemoryProvider:
    def __init__(self, indexer: EmbeddingIndexer) -> None:
        self.indexer = indexer

    def search(self, text: str, top_k: int = 5) -> List[Tuple[str, float]]:
        return self.indexer.query(text, top_k=top_k)


class NullVectorMemoryProvider:
    def search(self, text: str, top_k: int = 5) -> List[Tuple[str, float]]:
        _ = text
        _ = top_k
        return []


class StoreBackedStateProvider:
    def __init__(self, store: SQLiteStore, engine: DeterministicStateEngine) -> None:
        self.store = store
        self.engine = engine

    def get_state(self) -> UserStateSnapshot:
        return self.engine.calculate_from_store(self.store)
