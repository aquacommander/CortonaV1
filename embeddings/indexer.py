from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

from core.canonical_schema import CanonicalObject
from embeddings.models import EmbeddingModel
from embeddings.structured_text import build_structured_embedding_text
from embeddings.vector_store import VectorStore
from storage.sqlite_store import SQLiteStore


@dataclass(frozen=True)
class IndexedDocument:
    canonical_id: str
    text: str


@dataclass(frozen=True)
class EmbeddingIndexReport:
    indexed_count: int
    vector_dimension: int


def build_embedding_documents(objects: Sequence[CanonicalObject]) -> List[IndexedDocument]:
    documents = [
        IndexedDocument(
            canonical_id=obj.canonical_id,
            text=build_structured_embedding_text(obj),
        )
        for obj in objects
    ]
    return sorted(documents, key=lambda doc: doc.canonical_id)


class EmbeddingIndexer:
    """Embeds canonical memory and persists vectors to local store."""

    def __init__(self, model: EmbeddingModel, vector_store: VectorStore) -> None:
        self.model = model
        self.vector_store = vector_store

    def rebuild(self, objects: Sequence[CanonicalObject]) -> EmbeddingIndexReport:
        documents = build_embedding_documents(objects)
        if not documents:
            raise ValueError("No canonical objects available to index")

        texts = [doc.text for doc in documents]
        canonical_ids = [doc.canonical_id for doc in documents]
        vectors = self.model.embed_texts(texts)
        if len(vectors) != len(canonical_ids):
            raise ValueError("Embedding model returned vector count mismatch")
        if not vectors or not vectors[0]:
            raise ValueError("Embedding model returned empty vectors")

        self.vector_store.rebuild(canonical_ids, vectors)
        return EmbeddingIndexReport(indexed_count=len(canonical_ids), vector_dimension=len(vectors[0]))

    def rebuild_from_store(self, store: SQLiteStore) -> EmbeddingIndexReport:
        return self.rebuild(store.fetch_canonical_objects())

    def query(self, text: str, top_k: int = 5) -> List[Tuple[str, float]]:
        vectors = self.model.embed_texts([text])
        if not vectors:
            return []
        return self.vector_store.search(vectors[0], top_k=top_k)
