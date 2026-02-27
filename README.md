# Cortona Cognitive Orchestration Backend

Local-first architecture for deterministic memory normalization and persistent cognition.

## Layered Structure

- `core/`: canonical schema and deterministic shared primitives.
- `ingestion/`: source-specific deterministic mappers (no AI logic).
- `storage/`: local persistence adapters (SQLite planned).
- `graph/`: relational link construction on canonical memory.
- `embeddings/`: local vectorization after canonical persistence.
- `state/`: behavioral state derivation from structured patterns.
- `agents/`: event-driven agent interfaces and execution contracts.
- `tools/`: tool adapters callable by event-driven agents.
- `api/`: transport and orchestration entry points.

## Current Scope (Implemented)

- Canonical schema: `core/canonical_schema.py`
- Deterministic ID generation: `core/deterministic_id.py`
- Deterministic source mappers:
  - `ingestion/notes_mapper.py`
  - `ingestion/calendar_mapper.py`
  - `ingestion/reminders_mapper.py`
- SQLite storage and relations schema:
  - `storage/sqlite_store.py`
- Deterministic graph relation builder:
  - `graph/relation_builder.py`
- End-to-end deterministic orchestrator:
  - `api/pipeline_runner.py`
- Local embeddings stack (Step 6):
  - `embeddings/structured_text.py`
  - `embeddings/models.py`
  - `embeddings/faiss_store.py`
  - `embeddings/indexer.py`
  - `api/embeddings_runner.py`

## Design Constraints

- Schema-first and deterministic ingestion.
- No LLM or probabilistic logic in ingestion.
- Embeddings generated only after canonical storage.
- Local-first processing and storage.
- Layer separation to keep modules independently testable.
