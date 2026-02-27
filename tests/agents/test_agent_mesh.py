from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence, Tuple

from agents.builtin_agents import FollowUpPlannerAgent, MemoryContextAgent
from agents.contracts import AgentEvent
from agents.mesh import AgentMesh
from state.models import StateFeatures, UserStateSnapshot
from tools.registry import ToolRegistry, ToolResult


class FakeGraphMemoryProvider:
    def __init__(self) -> None:
        self.last_ids: List[str] = []

    def get_relations(self, canonical_ids: Sequence[str]) -> List[Dict[str, Any]]:
        self.last_ids = list(canonical_ids)
        return [
            {
                "relation_id": "rel_1",
                "from_canonical_id": "co_a",
                "to_canonical_id": "co_b",
                "relation_type": "FOLLOW_UP",
                "reason": "delta_hours=4.00",
                "confidence": 1.0,
                "created_at": "2026-02-27T10:00:00+00:00",
            }
        ]


class FakeVectorMemoryProvider:
    def __init__(self) -> None:
        self.queries: List[str] = []

    def search(self, text: str, top_k: int = 5) -> List[Tuple[str, float]]:
        _ = top_k
        self.queries.append(text)
        return [("co_a", 0.88)]


class FakeStateProvider:
    def get_state(self) -> UserStateSnapshot:
        return UserStateSnapshot(
            energy_level=70.0,
            stress_probability=0.2,
            focus_index=64.0,
            execution_velocity=55.0,
            domain_context="work",
            computed_at=datetime(2026, 2, 27, 12, 0, tzinfo=timezone.utc),
            features=StateFeatures(
                recent_object_count=3,
                upcoming_24h_count=1,
                overdue_reminder_count=0,
                follow_up_relation_count=1,
                active_domain_count=1,
            ),
            diagnostics={"context_switch_ratio": 0.33},
        )


def test_agent_mesh_dispatches_event_and_executes_tools() -> None:
    graph_memory = FakeGraphMemoryProvider()
    vector_memory = FakeVectorMemoryProvider()
    state_provider = FakeStateProvider()
    tools = ToolRegistry()
    tools.register("create_task", lambda payload: ToolResult(ok=True, output={"task": dict(payload)}))

    mesh = AgentMesh(
        agents=[FollowUpPlannerAgent(), MemoryContextAgent()],
        graph_memory=graph_memory,
        vector_memory=vector_memory,
        state_provider=state_provider,
        tool_registry=tools,
    )
    event = AgentEvent(
        event_type="RELATION_GRAPH_UPDATED",
        emitted_at=datetime(2026, 2, 27, 12, 30, tzinfo=timezone.utc),
        payload={"canonical_ids": ["co_a"], "query": "roadmap follow up"},
    )

    outcomes = mesh.dispatch(event)
    assert len(outcomes) == 2
    assert graph_memory.last_ids == ["co_a"]
    assert vector_memory.queries == ["roadmap follow up"]

    follow_up_outcome = next(outcome for outcome in outcomes if outcome.agent_name == "follow_up_planner")
    assert len(follow_up_outcome.tool_calls) == 1
    assert len(follow_up_outcome.tool_results) == 1
    assert follow_up_outcome.tool_results[0].ok is True

    context_outcome = next(outcome for outcome in outcomes if outcome.agent_name == "memory_context_agent")
    assert any("vector_hits=" in note for note in context_outcome.notes)
    assert any("relation_edges=" in note for note in context_outcome.notes)
