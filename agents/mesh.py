from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Sequence

from agents.contracts import (
    Agent,
    AgentContext,
    AgentEvent,
    AgentOutcome,
    GraphMemoryProvider,
    StateProvider,
    VectorMemoryProvider,
)
from tools.registry import ToolRegistry


class AgentMesh:
    """Event-driven multi-agent dispatcher for local cognitive workflows."""

    def __init__(
        self,
        *,
        agents: Sequence[Agent],
        graph_memory: GraphMemoryProvider,
        vector_memory: VectorMemoryProvider,
        state_provider: StateProvider,
        tool_registry: ToolRegistry,
    ) -> None:
        self.agents = list(agents)
        self.graph_memory = graph_memory
        self.vector_memory = vector_memory
        self.state_provider = state_provider
        self.tool_registry = tool_registry

    def dispatch(self, event: AgentEvent) -> List[AgentOutcome]:
        canonical_ids = self._extract_canonical_ids(event)
        query_text = self._extract_query_text(event)
        context = AgentContext(
            user_state=self.state_provider.get_state(),
            related_relations=self.graph_memory.get_relations(canonical_ids),
            vector_hits=self.vector_memory.search(query_text, top_k=5) if query_text else [],
            available_tools=sorted(self.tool_registry.list_tools().keys()),
        )

        outcomes: List[AgentOutcome] = []
        for agent in self.agents:
            if not agent.handles(event):
                continue
            draft = agent.handle(event, context)
            executed_tool_results = [
                self.tool_registry.execute(tool_call) for tool_call in draft.tool_calls
            ]
            outcomes.append(
                AgentOutcome(
                    agent_name=draft.agent_name,
                    emitted_events=list(draft.emitted_events),
                    tool_calls=list(draft.tool_calls),
                    tool_results=executed_tool_results,
                    notes=list(draft.notes),
                )
            )
        return outcomes

    def run(self, seed_events: Sequence[AgentEvent], *, max_events: int = 50) -> List[AgentOutcome]:
        queue = list(seed_events)
        outcomes: List[AgentOutcome] = []
        processed = 0
        while queue and processed < max_events:
            event = queue.pop(0)
            event_outcomes = self.dispatch(event)
            outcomes.extend(event_outcomes)
            for outcome in event_outcomes:
                queue.extend(outcome.emitted_events)
            processed += 1
        return outcomes

    @staticmethod
    def make_event(event_type: str, payload: Dict[str, object]) -> AgentEvent:
        return AgentEvent(
            event_type=event_type,
            emitted_at=datetime.now(timezone.utc),
            payload=payload,
        )

    @staticmethod
    def _extract_canonical_ids(event: AgentEvent) -> List[str]:
        raw = event.payload.get("canonical_ids")
        if isinstance(raw, list):
            return [str(item) for item in raw if str(item).strip()]
        single = event.payload.get("canonical_id")
        if single is None:
            return []
        value = str(single).strip()
        return [value] if value else []

    @staticmethod
    def _extract_query_text(event: AgentEvent) -> str:
        for key in ("query", "text", "title", "content"):
            value = event.payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""
