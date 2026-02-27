from __future__ import annotations

from dataclasses import dataclass

from embeddings.faiss_store import LocalFaissStore
from embeddings.indexer import EmbeddingIndexer
from embeddings.models import SentenceTransformerEmbeddingModel
from storage.sqlite_store import SQLiteStore


@dataclass(frozen=True)
class EmbeddingRunReport:
    indexed_count: int
    vector_dimension: int
    index_path: str
    metadata_path: str


def rebuild_local_embeddings(
    *,
    db_path: str,
    index_path: str,
    metadata_path: str,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    local_files_only: bool = False,
) -> EmbeddingRunReport:
    store = SQLiteStore(db_path)
    model = SentenceTransformerEmbeddingModel(
        model_name=model_name,
        local_files_only=local_files_only,
    )
    vector_store = LocalFaissStore(index_path=index_path, metadata_path=metadata_path)
    indexer = EmbeddingIndexer(model=model, vector_store=vector_store)
    report = indexer.rebuild_from_store(store)
    return EmbeddingRunReport(
        indexed_count=report.indexed_count,
        vector_dimension=report.vector_dimension,
        index_path=index_path,
        metadata_path=metadata_path,
    )
