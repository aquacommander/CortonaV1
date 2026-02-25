# CortonaV1 — Local Data Ingestion & Normalization

CortonaV1 is a **local-first data ingestion and normalization prototype**.

The goal of this repository is to take **unorganized personal data** from multiple sources and transform it into a **clean, canonical, machine-readable structure** — without using AI, embeddings, or LLMs.

This is the **foundation layer** for future systems (search, analytics, agents, AI), but this repo intentionally focuses only on **deterministic data engineering**.

---

## Scope (Very Important)

### What this project DOES
- Ingest raw data exactly as it exists
- Preserve original structure and metadata
- Normalize different data sources into a shared schema
- Run fully **locally**
- Use only standard Python data tooling

### What this project DOES NOT do
- ❌ No LLMs
- ❌ No embeddings
- ❌ No RAG
- ❌ No summarization
- ❌ No interpretation or inference

This project answers one question only:

> “How do we turn messy personal data into something structured and understandable?”

---

## Data Sources

Current supported sources:

- **Apple Notes**
- **Apple Reminders**
- **Google Calendar**

Each source is ingested independently and normalized into a shared canonical format.

---

## Project Structure

```text
local-ingest/
├── ingest/
│   ├── base.py                # Shared ingestion interfaces / helpers
│   ├── apple_notes.py         # Apple Notes ingestion
│   ├── apple_reminders.py     # Apple Reminders ingestion
│   └── google_calendar.py     # Google Calendar ingestion
│
├── normalize/
│   └── canonical_event.py     # Canonical schema + normalization logic
│
├── storage/
│   ├── raw/                   # Raw, untouched source data
│   └── normalized/            # Canonical, normalized output
│
├── main.py                    # Entry point
└── README.md