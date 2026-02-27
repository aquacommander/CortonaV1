# Changelog

All notable changes to this project are documented in this file.

## [0.2.0] - 2026-02-27

### Added
- Deterministic state engine (`energy_level`, `stress_probability`, `focus_index`, `execution_velocity`, `domain_context`).
- Event-driven agent mesh with graph/vector/state providers and local tool execution.
- Built-in local tools (`create_task`, `append_log`, `save_note_snapshot`).
- Full-cycle orchestrator (`scripts/run_cognitive_cycle.py`) with layer metrics output.
- Local telemetry logger writing JSONL metrics per layer action.
- CI workflow with lint, typing, tests, and smoke-cycle gate.
- Architecture and API contract documentation.

### Changed
- README expanded into a practical local runbook with expected outputs and troubleshooting.
- Project quality standards upgraded with `ruff` and `mypy` configuration.

### Notes
- Embeddings remain optional and are intentionally separated from ingestion/storage.
