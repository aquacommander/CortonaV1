from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping

from tools.registry import ToolRegistry, ToolResult


def _read_json_list(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError(f"expected JSON array in {path}")
    return [entry for entry in data if isinstance(entry, dict)]


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, separators=(",", ": ")),
        encoding="utf-8",
    )


def build_local_tool_registry(data_dir: str) -> ToolRegistry:
    root = Path(data_dir)
    tasks_path = root / "agent_tasks.json"
    logs_path = root / "agent_events.log"
    snapshots_path = root / "agent_note_snapshots.json"

    registry = ToolRegistry()

    def create_task(payload: Mapping[str, Any]) -> ToolResult:
        title = str(payload.get("title") or "").strip()
        if not title:
            return ToolResult(ok=False, output=None, error="title is required")
        details = str(payload.get("details") or "")
        domain = str(payload.get("domain") or "general")

        tasks = _read_json_list(tasks_path)
        task = {
            "task_id": f"task_{len(tasks) + 1:06d}",
            "title": title,
            "details": details,
            "domain": domain,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        tasks.append(task)
        _write_json(tasks_path, tasks)
        return ToolResult(ok=True, output=task)

    def append_log(payload: Mapping[str, Any]) -> ToolResult:
        message = str(payload.get("message") or "").strip()
        if not message:
            return ToolResult(ok=False, output=None, error="message is required")
        logs_path.parent.mkdir(parents=True, exist_ok=True)
        with logs_path.open("a", encoding="utf-8") as file:
            file.write(f"{datetime.now(timezone.utc).isoformat()} | {message}\n")
        return ToolResult(ok=True, output={"written": True})

    def save_note_snapshot(payload: Mapping[str, Any]) -> ToolResult:
        canonical_id = str(payload.get("canonical_id") or "").strip()
        note = str(payload.get("note") or "").strip()
        if not canonical_id or not note:
            return ToolResult(ok=False, output=None, error="canonical_id and note are required")
        snapshots = _read_json_list(snapshots_path)
        snapshot = {
            "canonical_id": canonical_id,
            "note": note,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        snapshots.append(snapshot)
        _write_json(snapshots_path, snapshots)
        return ToolResult(ok=True, output=snapshot)

    registry.register("create_task", create_task)
    registry.register("append_log", append_log)
    registry.register("save_note_snapshot", save_note_snapshot)
    return registry
