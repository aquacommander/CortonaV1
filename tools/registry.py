from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, MutableMapping, Protocol


@dataclass(frozen=True)
class ToolCall:
    tool_name: str
    payload: Mapping[str, Any]


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    output: Any
    error: str = ""


class ToolExecutor(Protocol):
    def __call__(self, payload: Mapping[str, Any]) -> ToolResult:
        ...


class ToolRegistry:
    """Deterministic registry and dispatcher for event-driven agents."""

    def __init__(self) -> None:
        self._tools: MutableMapping[str, ToolExecutor] = {}

    def register(self, name: str, executor: ToolExecutor) -> None:
        normalized = name.strip().lower()
        if not normalized:
            raise ValueError("tool name cannot be empty")
        self._tools[normalized] = executor

    def has(self, name: str) -> bool:
        return name.strip().lower() in self._tools

    def execute(self, call: ToolCall) -> ToolResult:
        normalized = call.tool_name.strip().lower()
        if normalized not in self._tools:
            return ToolResult(ok=False, output=None, error=f"tool not found: {call.tool_name}")
        return self._tools[normalized](call.payload)

    def list_tools(self) -> Dict[str, Callable[..., ToolResult]]:
        return dict(self._tools)
