# CortonaV1 Local Ingest Prototype

`local-ingest/` is a local-first data ingestion and normalization pipeline.

The design goal is narrow and explicit: ingest unorganized personal exports and
normalize them into one canonical schema with deterministic logic.

## Scope

### What this prototype does
- Ingests source exports from local JSON files.
- Preserves raw payloads in `storage/raw/` without cleaning or inference.
- Normalizes notes, reminders, and calendar events into one schema.
- Writes normalized output to `storage/normalized/`.

### What this prototype intentionally does not do
- No AI, LLMs, embeddings, vector databases, or cloud services.
- No summarization, inference, scoring, or interpretation.
- No automatic external fetching or syncing from remote APIs.

## Project Structure

```text
local-ingest/
├── ingest/
│   ├── base.py
│   ├── apple_notes.py
│   ├── apple_reminders.py
│   └── google_calendar.py
├── normalize/
│   └── canonical_event.py
├── storage/
│   ├── raw/
│   └── normalized/
├── main.py
└── README.md
```

## Data Flow

1. **Ingestion step** (`ingest/*`)
   - Reads a local JSON export file.
   - Writes a snapshot document to `storage/raw/` with:
     - `source`
     - `source_file`
     - `ingested_at_utc`
     - `payload` (untouched source payload)

2. **Normalization step** (`normalize/canonical_event.py`)
   - Reads each raw snapshot.
   - Maps records to canonical fields using explicit source-specific mappings.
   - Preserves full original source record in `raw_record`.
   - Writes per-source output and a combined `canonical_all.json`.

## Canonical Schema

Each normalized record includes:
- `canonical_id`
- `source_system`
- `source_record_type` (`note`, `task`, `event`)
- `source_record_id`
- `title`
- `content`
- `start_at`
- `end_at`
- `due_at`
- `created_at`
- `updated_at`
- `status`
- `location`
- `labels`
- `participants`
- `extra`
- `raw_record`

This keeps the schema explicit while retaining source fidelity.

## Expected Input Shape

The ingestors accept JSON payloads from local exports.

- Apple Notes: either `[{...}, {...}]` or `{"notes": [{...}]}`
- Apple Reminders: either `[{...}]` or `{"reminders": [{...}]}`
- Google Calendar: either `[{...}]` or `{"events": [{...}]}`

No field cleaning is performed during ingestion.

## Run

From the repository root:

```bash
python local-ingest/main.py \
  --apple-notes-file path/to/apple_notes.json \
  --apple-reminders-file path/to/apple_reminders.json \
  --google-calendar-file path/to/google_calendar.json
```

You can provide any subset of source files. Only provided sources are ingested
and normalized.

## Notes for Engineers

- The system is deterministic by construction: same input file content and order
  produce the same normalized semantic output.
- Mapping logic is intentionally verbose and straightforward to review.
- If new data sources are added, implement a new ingestor and a new explicit
  mapper function in `canonical_event.py`.
