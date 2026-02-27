from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict


@dataclass(frozen=True)
class StateFeatures:
    recent_object_count: int
    upcoming_24h_count: int
    overdue_reminder_count: int
    follow_up_relation_count: int
    active_domain_count: int


@dataclass(frozen=True)
class UserStateSnapshot:
    energy_level: float
    stress_probability: float
    focus_index: float
    execution_velocity: float
    domain_context: str
    computed_at: datetime
    features: StateFeatures
    diagnostics: Dict[str, float] = field(default_factory=dict)
