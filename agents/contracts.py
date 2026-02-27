from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Mapping, Protocol, Sequence, Tuple

from state.models import UserStateSnapshot
from tools.registry import ToolCall, ToolResult


@dataclass(frozen=True)
class AgentEvent:
    event_type: str
    emitted_at: datetime
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentContext:
    user_state: UserStateSnapshot
    related_relations: Sequence[Dict[str, Any]]
    vector_hits: Sequence[Tuple[str, float]]
    available_tools: Sequence[str]


@dataclass(frozen=True)
class AgentOutcome:
    agent_name: str
    emitted_events: Sequence[AgentEvent] = field(default_factory=list)
    tool_calls: Sequence[ToolCall] = field(default_factory=list)
    tool_results: Sequence[ToolResult] = field(default_factory=list)
    notes: Sequence[str] = field(default_factory=list)


class Agent(Protocol):
    name: str

    def handles(self, event: AgentEvent) -> bool:
        ...

    def handle(self, event: AgentEvent, context: AgentContext) -> AgentOutcome:
        ...


class GraphMemoryProvider(Protocol):
    def get_relations(self, canonical_ids: Sequence[str]) -> List[Dict[str, Any]]:
        ...


class VectorMemoryProvider(Protocol):
    def search(self, text: str, top_k: int = 5) -> List[Tuple[str, float]]:
        ...


class StateProvider(Protocol):
    def get_state(self) -> UserStateSnapshot:
        ...
