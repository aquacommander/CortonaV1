from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Sequence, Tuple


def _ensure_2d_float32(vectors: Sequence[Sequence[float]]) -> Any:
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("numpy is required for FAISS vector storage. Install with: pip install .[embeddings]") from exc

    array = np.asarray(vectors, dtype=np.float32)
    if array.ndim != 2:
        raise ValueError("vectors must be a 2D array-like structure")
    return array


def _normalize_rows(vectors: Any) -> Any:
    import numpy as np

    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return vectors / norms


class LocalFaissStore:
    """Persistent local FAISS index with canonical ID metadata."""

    def __init__(self, index_path: str, metadata_path: str) -> None:
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_faiss(self) -> Any:
        try:
            import faiss
        except ImportError as exc:
            raise RuntimeError(
                "faiss is required for vector indexing. Install optional deps with: pip install .[embeddings]"
            ) from exc
        return faiss

    def rebuild(self, canonical_ids: Sequence[str], vectors: Sequence[Sequence[float]]) -> None:
        if len(canonical_ids) != len(vectors):
            raise ValueError("canonical_ids and vectors must have the same length")
        if not canonical_ids:
            raise ValueError("cannot build FAISS index with zero vectors")

        vector_array = _ensure_2d_float32(vectors)
        vector_array = _normalize_rows(vector_array)
        dimension = int(vector_array.shape[1])

        faiss = self._load_faiss()
        index = faiss.IndexFlatIP(dimension)
        index.add(vector_array)
        faiss.write_index(index, str(self.index_path))

        metadata = {"dimension": dimension, "canonical_ids": list(canonical_ids)}
        self.metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=True, separators=(",", ":"), indent=2),
            encoding="utf-8",
        )

    def search(self, query_vector: Sequence[float], top_k: int = 5) -> List[Tuple[str, float]]:
        if top_k <= 0:
            return []
        if not self.index_path.exists() or not self.metadata_path.exists():
            return []

        faiss = self._load_faiss()
        metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        canonical_ids = metadata["canonical_ids"]
        dimension = int(metadata["dimension"])

        query_array = _ensure_2d_float32([query_vector])
        if query_array.shape[1] != dimension:
            raise ValueError(
                f"query vector dimension mismatch: expected {dimension}, got {query_array.shape[1]}"
            )
        query_array = _normalize_rows(query_array)

        index = faiss.read_index(str(self.index_path))
        distances, indices = index.search(query_array, top_k)

        results: List[Tuple[str, float]] = []
        for idx, score in zip(indices[0], distances[0]):
            if idx < 0:
                continue
            if idx >= len(canonical_ids):
                continue
            results.append((canonical_ids[idx], float(score)))
        return results

    def count(self) -> int:
        if not self.metadata_path.exists():
            return 0
        metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        return len(metadata.get("canonical_ids", []))
