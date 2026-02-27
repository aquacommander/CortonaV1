from __future__ import annotations

from typing import List, Protocol, Sequence


class EmbeddingModel(Protocol):
    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        """Return one embedding vector per input text."""


class SentenceTransformerEmbeddingModel:
    """Local sentence-transformer embedder (no cloud calls)."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        *,
        device: str = "cpu",
        local_files_only: bool = False,
        normalize_embeddings: bool = True,
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required for local embedding generation. "
                "Install optional deps with: pip install .[embeddings]"
            ) from exc

        self._normalize_embeddings = normalize_embeddings
        self._model = SentenceTransformer(
            model_name,
            device=device,
            local_files_only=local_files_only,
        )

    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        encoded = self._model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=self._normalize_embeddings,
        )
        return encoded.tolist()
