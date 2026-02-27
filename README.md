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

## Verify Each Step (Client Demo Commands)

Run these from project root in PowerShell after venv activation.

### Step 1: Verify structure

```powershell
ls
```

Expected: folders `core`, `ingestion`, `storage`, `graph`, `embeddings`, `state`, `agents`, `tools`, `api`, `scripts`, `tests`.

Sample result:

```text
Directory: F:\...\Cortona
core  ingestion  storage  graph  embeddings  state  agents  tools  api  scripts  tests
```

### Step 2: Verify canonical schema

```powershell
python -c "from core import CanonicalObject; o=CanonicalObject(canonical_id='co_demo',source_system='apple_notes',source_record_type='note'); print(o)"
```

Expected: printed `CanonicalObject` with canonical fields (`title`, `content`, timestamps, `people`, `labels`, `domain`).

Sample result:

```text
canonical_id='co_demo' source_system='apple_notes' source_record_type='note' title='' content='' start_at=None end_at=None due_at=None created_at=None updated_at=None people=[] labels=[] domain='general'
```

### Step 3: Verify deterministic ingestion mappers

```powershell
python -c "import json; from ingestion.notes_mapper import map_notes; d=json.load(open('notes.json','r',encoding='utf-8')); x=map_notes(d['notes'])[0]; print(x.canonical_id, x.source_system, x.source_record_type, x.title)"
python -c "import json; from ingestion.calendar_mapper import map_events; d=json.load(open('calendar.json','r',encoding='utf-8')); x=map_events(d['events'])[0]; print(x.canonical_id, x.source_system, x.source_record_type, x.start_at)"
python -c "import json; from ingestion.reminders_mapper import map_reminders; d=json.load(open('reminders.json','r',encoding='utf-8')); x=map_reminders(d['reminders'])[0]; print(x.canonical_id, x.source_system, x.source_record_type, x.due_at)"
```

Expected: each command prints a deterministic `co_...` ID and normalized canonical fields.

Sample result:

```text
co_2f6b1c... apple_notes note Roadmap Notes
co_3c91aa... google_calendar event 2026-02-27 11:00:00+00:00
co_90bb4d... apple_reminders reminder 2026-02-28 10:00:00+00:00
```

### Step 4: Verify local SQLite storage

```powershell
python -c "from api.pipeline_runner import run_pipeline_from_files; r=run_pipeline_from_files(db_path='data/cortona.db', notes_path='notes.json', calendar_path='calendar.json', reminders_path='reminders.json'); print(r)"
python -c "import sqlite3; c=sqlite3.connect('data/cortona.db'); cur=c.cursor(); print('canonical_objects=',cur.execute('select count(*) from canonical_objects').fetchone()[0]); print('relations=',cur.execute('select count(*) from relations').fetchone()[0]); c.close()"
```

Expected: `canonical_count` > 0 and database tables populated.

Sample result:

```text
PipelineRunReport(notes_count=1, calendar_count=1, reminders_count=1, canonical_count=3, relation_count=10, db_path='data/cortona.db')
canonical_objects= 3
relations= 10
```

### Step 5: Verify relation graph

```powershell
python -c "import sqlite3; c=sqlite3.connect('data/cortona.db'); cur=c.cursor(); print(cur.execute('select relation_type, count(*) from relations group by relation_type').fetchall()); c.close()"
```

Expected relation types include `SAME_DAY`, `SAME_PERSON`, `SAME_DOMAIN`, `FOLLOW_UP`.

Sample result:

```text
[('FOLLOW_UP', 3), ('SAME_DAY', 1), ('SAME_DOMAIN', 3), ('SAME_PERSON', 3)]
```

### Step 6: Verify embeddings (optional, requires extra deps)

```powershell
python -c "from api.embeddings_runner import rebuild_local_embeddings; r=rebuild_local_embeddings(db_path='data/cortona.db', index_path='data/memory.faiss', metadata_path='data/memory.meta.json'); print(r)"
python -c "from embeddings.models import SentenceTransformerEmbeddingModel; from embeddings.faiss_store import LocalFaissStore; from embeddings.indexer import EmbeddingIndexer; i=EmbeddingIndexer(SentenceTransformerEmbeddingModel(), LocalFaissStore('data/memory.faiss','data/memory.meta.json')); print(i.query('roadmap follow up', top_k=3))"
```

Expected: index files created and query returns a list of `(canonical_id, score)` tuples.

Sample result:

```text
EmbeddingRunReport(indexed_count=3, vector_dimension=384, index_path='data/memory.faiss', metadata_path='data/memory.meta.json')
[('co_2f6b1c...', 0.78), ('co_3c91aa...', 0.64), ('co_90bb4d...', 0.59)]
```

### Step 7: Verify state engine

```powershell
python -c "from api.state_runner import compute_user_state; s=compute_user_state(db_path='data/cortona.db'); print(s)"
```

Expected: `energy_level`, `focus_index`, `execution_velocity` in `[0,100]`, `stress_probability` in `[0,1]`.

Sample result:

```text
UserStateSnapshot(energy_level=66.16, stress_probability=0.073, focus_index=70.66, execution_velocity=46.0, domain_context='work', ...)
```

### Step 8: Verify event-driven agent mesh

```powershell
python -c "from api.agent_mesh_runner import run_agent_mesh_event; out=run_agent_mesh_event(db_path='data/cortona.db', index_path='data/memory.faiss', metadata_path='data/memory.meta.json', event_type='RELATION_GRAPH_UPDATED', payload={'canonical_ids':['co_demo'],'query':'follow up priorities'}, data_dir='data'); print(out)"
```

Expected: list of `AgentOutcome` values, tool activity, and local artifacts in `data/`.

Sample result:

```text
[AgentOutcome(agent_name='follow_up_planner', ...), AgentOutcome(agent_name='memory_context_agent', ...)]
```

### Full end-to-end check (single command)

```powershell
python scripts/run_cognitive_cycle.py `
  --notes notes.json `
  --calendar calendar.json `
  --reminders reminders.json `
  --db data/final_check.db `
  --metrics data/final_check_metrics.jsonl `
  --skip-embeddings
```

Expected: JSON report with non-zero canonical and relation counts, state values, and agent outcomes.

Sample result:

```json
{
  "pipeline": {
    "canonical_count": 3,
    "relation_count": 10
  },
  "state": {
    "domain_context": "work",
    "energy_level": 66.16
  },
  "agent_outcomes_count": 2
}
```
