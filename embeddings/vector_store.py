from __future__ import annotations

from typing import List, Protocol, Sequence, Tuple


class VectorStore(Protocol):
    def rebuild(self, canonical_ids: Sequence[str], vectors: Sequence[Sequence[float]]) -> None:
        """Replace vector index with the provided canonical objects."""

    def search(self, query_vector: Sequence[float], top_k: int = 5) -> List[Tuple[str, float]]:
        """Return (canonical_id, similarity_score) tuples."""
