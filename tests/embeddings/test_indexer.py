from typing import List, Sequence, Tuple

from core.canonical_schema import CanonicalObject
from embeddings.indexer import EmbeddingIndexer, build_embedding_documents


class FakeEmbeddingModel:
    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            length_component = float(len(text))
            checksum_component = float(sum(ord(ch) for ch in text) % 1000)
            vectors.append([length_component, checksum_component, 1.0])
        return vectors


class FakeVectorStore:
    def __init__(self) -> None:
        self.canonical_ids: List[str] = []
        self.vectors: List[List[float]] = []

    def rebuild(self, canonical_ids: Sequence[str], vectors: Sequence[Sequence[float]]) -> None:
        self.canonical_ids = list(canonical_ids)
        self.vectors = [list(vector) for vector in vectors]

    def search(self, query_vector: Sequence[float], top_k: int = 5) -> List[Tuple[str, float]]:
        del query_vector
        return [(canonical_id, 1.0) for canonical_id in self.canonical_ids[:top_k]]


def test_build_embedding_documents_sorted_by_canonical_id() -> None:
    objects = [
        CanonicalObject(
            canonical_id="co_2",
            source_system="apple_notes",
            source_record_type="note",
            title="B",
            content="...",
            domain="work",
        ),
        CanonicalObject(
            canonical_id="co_1",
            source_system="apple_notes",
            source_record_type="note",
            title="A",
            content="...",
            domain="work",
        ),
    ]
    docs = build_embedding_documents(objects)
    assert [doc.canonical_id for doc in docs] == ["co_1", "co_2"]


def test_indexer_rebuild_and_query_with_fake_components() -> None:
    objects = [
        CanonicalObject(
            canonical_id="co_1",
            source_system="apple_notes",
            source_record_type="note",
            title="Roadmap",
            content="Ship Q2 plan.",
            people=["sam@example.com"],
            domain="work",
        ),
        CanonicalObject(
            canonical_id="co_2",
            source_system="google_calendar",
            source_record_type="event",
            title="Sync",
            content="Weekly planning sync.",
            people=["lee@example.com"],
            domain="work",
        ),
    ]
    model = FakeEmbeddingModel()
    store = FakeVectorStore()
    indexer = EmbeddingIndexer(model=model, vector_store=store)

    report = indexer.rebuild(objects)
    assert report.indexed_count == 2
    assert report.vector_dimension == 3

    results = indexer.query("roadmap planning", top_k=1)
    assert len(results) == 1
    assert results[0][0] == "co_1"
