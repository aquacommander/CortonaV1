import json

from tools.builtin_tools import build_local_tool_registry
from tools.registry import ToolCall


def test_local_tool_registry_creates_files_and_records(tmp_path) -> None:
    registry = build_local_tool_registry(str(tmp_path))

    create_result = registry.execute(
        ToolCall(
            tool_name="create_task",
            payload={"title": "Follow up", "details": "Ping team", "domain": "work"},
        )
    )
    assert create_result.ok is True

    log_result = registry.execute(
        ToolCall(tool_name="append_log", payload={"message": "graph updated"})
    )
    assert log_result.ok is True

    snapshot_result = registry.execute(
        ToolCall(
            tool_name="save_note_snapshot",
            payload={"canonical_id": "co_1", "note": "Pinned for review"},
        )
    )
    assert snapshot_result.ok is True

    tasks_path = tmp_path / "agent_tasks.json"
    snapshots_path = tmp_path / "agent_note_snapshots.json"
    logs_path = tmp_path / "agent_events.log"

    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    snapshots = json.loads(snapshots_path.read_text(encoding="utf-8"))
    logs = logs_path.read_text(encoding="utf-8")

    assert len(tasks) == 1
    assert tasks[0]["title"] == "Follow up"
    assert len(snapshots) == 1
    assert snapshots[0]["canonical_id"] == "co_1"
    assert "graph updated" in logs
