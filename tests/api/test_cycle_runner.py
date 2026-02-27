import json

from api.cycle_runner import run_cognitive_cycle_from_files


def test_run_cognitive_cycle_from_files_without_embeddings(tmp_path) -> None:
    notes_path = tmp_path / "notes.json"
    calendar_path = tmp_path / "calendar.json"
    reminders_path = tmp_path / "reminders.json"
    db_path = tmp_path / "cortona.db"
    metrics_path = tmp_path / "metrics.jsonl"

    notes_path.write_text(
        json.dumps(
            {
                "notes": [
                    {
                        "id": "n-1",
                        "title": "Roadmap notes",
                        "content": "Need follow-up with sam@example.com",
                        "created_at": "2026-02-27T09:00:00Z",
                        "people": ["sam@example.com"],
                        "folder": "work",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    calendar_path.write_text(
        json.dumps(
            {
                "events": [
                    {
                        "id": "e-1",
                        "summary": "Roadmap sync",
                        "description": "Discuss updates.",
                        "start": {"dateTime": "2026-02-27T11:00:00Z"},
                        "end": {"dateTime": "2026-02-27T11:30:00Z"},
                        "attendees": [{"email": "sam@example.com"}],
                        "calendar": "work",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    reminders_path.write_text(
        json.dumps(
            {
                "reminders": [
                    {
                        "id": "r-1",
                        "title": "Send recap",
                        "notes": "Share summary",
                        "dueDate": "2026-02-28T10:00:00Z",
                        "assignees": ["sam@example.com"],
                        "list": "work",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = run_cognitive_cycle_from_files(
        notes_path=str(notes_path),
        calendar_path=str(calendar_path),
        reminders_path=str(reminders_path),
        db_path=str(db_path),
        index_path=str(tmp_path / "memory.faiss"),
        metadata_path=str(tmp_path / "memory.meta.json"),
        metrics_path=str(metrics_path),
        rebuild_embeddings=False,
    )

    assert report.pipeline.canonical_count == 3
    assert report.pipeline.relation_count > 0
    assert report.state["domain_context"] == "work"
    assert report.agent_outcomes_count >= 1
    assert metrics_path.exists()
    assert report.embedding is None

    metric_lines = [
        json.loads(line)
        for line in metrics_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    layers = {metric["layer"] for metric in metric_lines}
    assert "pipeline" in layers
    assert "state" in layers
    assert "agents" in layers
