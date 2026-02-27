from __future__ import annotations

from typing import List

from agents.contracts import AgentContext, AgentEvent, AgentOutcome
from tools.registry import ToolCall


class FollowUpPlannerAgent:
    """Schedules concrete follow-up actions from deterministic memory events."""

    name = "follow_up_planner"

    def handles(self, event: AgentEvent) -> bool:
        return event.event_type in {"RELATION_GRAPH_UPDATED", "FOLLOW_UP_TRIGGERED"}

    def handle(self, event: AgentEvent, context: AgentContext) -> AgentOutcome:
        _ = event
        notes: List[str] = []
        tool_calls: List[ToolCall] = []

        follow_up_edges = [
            rel for rel in context.related_relations if rel.get("relation_type") == "FOLLOW_UP"
        ]
        if not follow_up_edges:
            notes.append("No follow-up relations in event scope.")
            return AgentOutcome(agent_name=self.name, notes=notes)

        if not context.available_tools or "create_task" not in context.available_tools:
            notes.append("create_task tool unavailable; follow-up actions not materialized.")
            return AgentOutcome(agent_name=self.name, notes=notes)

        domain_hint = context.user_state.domain_context
        for relation in follow_up_edges:
            from_id = str(relation.get("from_canonical_id") or "")
            to_id = str(relation.get("to_canonical_id") or "")
            reason = str(relation.get("reason") or "")
            tool_calls.append(
                ToolCall(
                    tool_name="create_task",
                    payload={
                        "title": f"Follow up: {from_id} -> {to_id}",
                        "details": reason,
                        "domain": domain_hint,
                    },
                )
            )
        notes.append(f"Queued {len(tool_calls)} deterministic follow-up task(s).")
        return AgentOutcome(agent_name=self.name, tool_calls=tool_calls, notes=notes)


class MemoryContextAgent:
    """Adds vector/graph context notes for non-chat event execution."""

    name = "memory_context_agent"

    def handles(self, event: AgentEvent) -> bool:
        return event.event_type in {"MEMORY_QUERY", "RELATION_GRAPH_UPDATED", "STATE_RECALCULATED"}

    def handle(self, event: AgentEvent, context: AgentContext) -> AgentOutcome:
        _ = event
        notes = [
            f"vector_hits={len(context.vector_hits)}",
            f"relation_edges={len(context.related_relations)}",
            f"state_domain={context.user_state.domain_context}",
            f"stress_probability={context.user_state.stress_probability:.3f}",
        ]
        return AgentOutcome(agent_name=self.name, notes=notes)
