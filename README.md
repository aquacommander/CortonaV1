# Cortona Cognitive Orchestration Backend

Local-first architecture for deterministic memory normalization and persistent cognition.

## Layered Structure

- `core/`: canonical schema, deterministic IDs, telemetry.
- `ingestion/`: source-specific deterministic mappers (no AI logic).
- `storage/`: local SQLite persistence.
- `graph/`: deterministic relational links from canonical memory.
- `embeddings/`: local embedding generation and FAISS index.
- `state/`: deterministic behavioral state engine.
- `agents/`: event-driven agent mesh and providers.
- `tools/`: local tool registry and built-in tool pack.
- `api/`: high-level runners for each pipeline layer.
- `scripts/`: operational entrypoints.

## What Is Implemented

- Steps 1-5: project scaffold, canonical schema, deterministic ingestion, SQLite storage, relation graph.
- Step 6: structured-text embeddings (`title + content + people + domain`) with local FAISS persistence.
- Step 7: deterministic state engine (`energy_level`, `stress_probability`, `focus_index`, `execution_velocity`, `domain_context`).
- Step 8: event-driven agent mesh that reads graph/vector/state and executes local tools.
- Full-cycle orchestration runner with layer metrics logging.

## Design Constraints

- Schema-first and deterministic ingestion.
- No LLM or probabilistic logic in ingestion.
- Embeddings generated only after canonical storage.
- Local-first processing and storage.
- Layer separation to keep modules independently testable.
- Agent orchestration is event-driven (not chat/session driven).

## Local Setup (Windows PowerShell)

### 1) Python and venv

Use Python 3.11 for best dependency compatibility.

```powershell
python --version
py -3.11 -m venv .venv
```

### 2) Activation policy fix (if blocked)

If activation fails with `PSSecurityException`, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3) Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install pydantic pytest
```

Optional embeddings dependencies:

```powershell
python -m pip install numpy faiss-cpu sentence-transformers
```

### 4) Validate install

```powershell
python -m pytest -q
```

Expected output should be similar to:

```text
...s.................                                                     [100%]
16 passed, 1 skipped
```

(`1 skipped` is normal when FAISS is not installed.)

## One-Command Cognitive Cycle

Use this when you want end-to-end execution:

```powershell
python scripts/run_cognitive_cycle.py `
  --notes notes.json `
  --calendar calendar.json `
  --reminders reminders.json `
  --db data/cortona.db `
  --index data/memory.faiss `
  --metadata data/memory.meta.json `
  --metrics data/metrics.jsonl
```

If you do not want embeddings yet:

```powershell
python scripts/run_cognitive_cycle.py `
  --notes notes.json `
  --calendar calendar.json `
  --reminders reminders.json `
  --skip-embeddings
```

## Expected Outputs

After a successful run, you should get:

- `data/cortona.db` (SQLite canonical + relations memory)
- `data/memory.faiss` and `data/memory.meta.json` (if embeddings run)
- `data/metrics.jsonl` (per-layer timing and status)
- `data/agent_tasks.json`, `data/agent_events.log`, `data/agent_note_snapshots.json` (agent tool outputs)

Cycle JSON output should include:

- `pipeline.canonical_count` > 0
- `pipeline.relation_count` >= 0
- `state.energy_level` in `[0, 100]`
- `state.stress_probability` in `[0, 1]`
- `agent_outcomes_count` >= 1

## Metrics and Logging

Layer metrics are written to `data/metrics.jsonl` as one JSON object per action:

- `pipeline` -> normalize/store
- `embeddings` -> rebuild index (if enabled)
- `state` -> compute state
- `agents` -> dispatch mesh event

Each line includes:
- `layer`, `action`, `started_at`, `ended_at`, `elapsed_ms`, `ok`, `details`

## Built-In Agent Tools

The local tool pack includes:

- `create_task`: appends pending tasks to `data/agent_tasks.json`
- `append_log`: appends event lines to `data/agent_events.log`
- `save_note_snapshot`: appends snapshots to `data/agent_note_snapshots.json`

These are deterministic local side effects for agent execution.

## Quality and CI

- Lint and style checks via `ruff`
- Type checks via `mypy`
- Unit tests via `pytest`
- CI workflow: `.github/workflows/ci.yml`

Run locally:

```powershell
python -m pip install -e ".[dev]"
ruff check .
mypy api agents core embeddings graph ingestion state storage tools
pytest -q
```

## Release Docs

- Changelog: `CHANGELOG.md`
- Architecture: `docs/ARCHITECTURE.md`
- API contracts: `docs/API_CONTRACTS.md`
