import pytest

from embeddings.faiss_store import LocalFaissStore


def test_faiss_store_rebuild_and_search_if_installed(tmp_path) -> None:
    pytest.importorskip("numpy")
    pytest.importorskip("faiss")

    store = LocalFaissStore(
        index_path=str(tmp_path / "memory.faiss"),
        metadata_path=str(tmp_path / "memory.meta.json"),
    )
    canonical_ids = ["co_1", "co_2", "co_3"]
    vectors = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.7, 0.7, 0.0],
    ]

    store.rebuild(canonical_ids, vectors)
    results = store.search([1.0, 0.0, 0.0], top_k=2)

    assert store.count() == 3
    assert len(results) == 2
    assert results[0][0] == "co_1"
