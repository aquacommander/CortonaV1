# API Contracts

This document defines stable contracts for orchestration entrypoints in `api/`.

## `run_pipeline_from_files(...)`

### Input
- `db_path: str`
- `notes_path: str`
- `calendar_path: str`
- `reminders_path: str`

### Output (`PipelineRunReport`)
- `notes_count: int`
- `calendar_count: int`
- `reminders_count: int`
- `canonical_count: int`
- `relation_count: int`
- `db_path: str`

## `rebuild_local_embeddings(...)`

### Input
- `db_path: str`
- `index_path: str`
- `metadata_path: str`
- `model_name: str`
- `local_files_only: bool`

### Output (`EmbeddingRunReport`)
- `indexed_count: int`
- `vector_dimension: int`
- `index_path: str`
- `metadata_path: str`

## `compute_user_state(...)`

### Input
- `db_path: str`
- `recent_window_days: int`
- `follow_up_window_days: int`

### Output (`UserStateSnapshot`)
- `energy_level: float` in `[0, 100]`
- `stress_probability: float` in `[0, 1]`
- `focus_index: float` in `[0, 100]`
- `execution_velocity: float` in `[0, 100]`
- `domain_context: str`
- `features: StateFeatures`
- `diagnostics: Dict[str, float]`

## `run_agent_mesh_event(...)`

### Input
- `db_path: str`
- `index_path: str`
- `metadata_path: str`
- `event_type: str`
- `payload: Dict[str, Any]`
- `model_name: str`
- `local_files_only: bool`
- `data_dir: str`

### Output
- `List[AgentOutcome]`

Each `AgentOutcome` includes:
- `agent_name`
- `emitted_events`
- `tool_calls`
- `tool_results`
- `notes`

## `run_cognitive_cycle_from_files(...)`

### Input
- export file paths (`notes`, `calendar`, `reminders`)
- output paths (`db`, `index`, `metadata`, `metrics`)
- toggles for embeddings and model loading

### Output (`CognitiveCycleReport`)
- `pipeline: PipelineRunReport`
- `state: Dict[str, Any]`
- `agent_outcomes_count: int`
- `agent_notes: List[str]`
- `embedding: Optional[EmbeddingRunReport]`
- `embedding_error: str`
- output paths (`metrics_path`, `db_path`, `index_path`, `metadata_path`)

## Stability Policy

- Backward-compatible additions to report fields are allowed.
- Removing or renaming current fields requires a major version bump and migration notes.
