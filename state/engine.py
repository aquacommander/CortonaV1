from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, Optional, Sequence, Set

from core.canonical_schema import CanonicalObject
from state.models import StateFeatures, UserStateSnapshot
from storage.sqlite_store import SQLiteStore

FOLLOW_UP = "FOLLOW_UP"


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _as_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _anchor_datetime(obj: CanonicalObject) -> Optional[datetime]:
    return _as_utc(obj.start_at or obj.due_at or obj.updated_at or obj.created_at or obj.end_at)


def _relation_time_hint(relation: Dict[str, object]) -> Optional[datetime]:
    value = relation.get("created_at")
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip().replace("Z", "+00:00")
    try:
        return _as_utc(datetime.fromisoformat(candidate))
    except ValueError:
        return None


@dataclass(frozen=True)
class StateEngineConfig:
    recent_window_days: int = 7
    follow_up_window_days: int = 7


class DeterministicStateEngine:
    """Derives behavior state from structured memory patterns only."""

    def __init__(self, config: Optional[StateEngineConfig] = None) -> None:
        self.config = config or StateEngineConfig()

    def calculate(
        self,
        objects: Sequence[CanonicalObject],
        relations: Iterable[Dict[str, object]],
        *,
        now: Optional[datetime] = None,
    ) -> UserStateSnapshot:
        current_time = _as_utc(now or datetime.now(timezone.utc))
        assert current_time is not None
        recent_floor = current_time - timedelta(days=self.config.recent_window_days)
        follow_up_floor = current_time - timedelta(days=self.config.follow_up_window_days)

        recent_objects = [obj for obj in objects if self._is_recent(obj, recent_floor)]
        recent_ids: Set[str] = {obj.canonical_id for obj in recent_objects}

        overdue_reminder_count = sum(1 for obj in recent_objects if self._is_overdue_reminder(obj, current_time))
        upcoming_24h_count = sum(1 for obj in recent_objects if self._is_upcoming(obj, current_time))
        active_domain_count = len({obj.domain.strip().lower() for obj in recent_objects if obj.domain.strip()})
        domain_context = self._resolve_domain_context(recent_objects)

        follow_up_relation_count = 0
        for relation in relations:
            relation_type = str(relation.get("relation_type") or "")
            if relation_type != FOLLOW_UP:
                continue
            from_id = str(relation.get("from_canonical_id") or "")
            to_id = str(relation.get("to_canonical_id") or "")
            if from_id not in recent_ids and to_id not in recent_ids:
                continue
            relation_time = _relation_time_hint(relation)
            if relation_time is not None and relation_time < follow_up_floor:
                continue
            follow_up_relation_count += 1

        recent_object_count = len(recent_objects)
        context_switch_ratio = (
            float(active_domain_count) / float(recent_object_count) if recent_object_count else 0.0
        )
        follow_up_density = (
            float(follow_up_relation_count) / float(recent_object_count) if recent_object_count else 0.0
        )

        energy_level = _clamp(
            55.0
            + 3.5 * recent_object_count
            - 8.0 * overdue_reminder_count
            - 2.0 * upcoming_24h_count
            - 10.0 * context_switch_ratio
            + 6.0 * follow_up_density,
            0.0,
            100.0,
        )
        focus_index = _clamp(
            72.0
            - 25.0 * context_switch_ratio
            + 8.0 * follow_up_density
            - 1.0 * upcoming_24h_count,
            0.0,
            100.0,
        )
        execution_velocity = _clamp(
            20.0 + 6.0 * recent_object_count + 8.0 * follow_up_density - 2.0 * overdue_reminder_count,
            0.0,
            100.0,
        )
        stress_probability = _clamp(
            0.15
            + 0.12 * overdue_reminder_count
            + 0.04 * upcoming_24h_count
            + 0.25 * context_switch_ratio
            - 0.20 * follow_up_density
            + (0.35 if energy_level < 35.0 else 0.0),
            0.0,
            1.0,
        )

        features = StateFeatures(
            recent_object_count=recent_object_count,
            upcoming_24h_count=upcoming_24h_count,
            overdue_reminder_count=overdue_reminder_count,
            follow_up_relation_count=follow_up_relation_count,
            active_domain_count=active_domain_count,
        )
        diagnostics: Dict[str, float] = {
            "context_switch_ratio": context_switch_ratio,
            "follow_up_density": follow_up_density,
        }
        return UserStateSnapshot(
            energy_level=energy_level,
            stress_probability=stress_probability,
            focus_index=focus_index,
            execution_velocity=execution_velocity,
            domain_context=domain_context,
            computed_at=current_time,
            features=features,
            diagnostics=diagnostics,
        )

    def calculate_from_store(self, store: SQLiteStore, *, now: Optional[datetime] = None) -> UserStateSnapshot:
        objects = store.fetch_canonical_objects()
        relations = store.fetch_relations()
        return self.calculate(objects, relations, now=now)

    @staticmethod
    def _is_recent(obj: CanonicalObject, recent_floor: datetime) -> bool:
        anchor = _anchor_datetime(obj)
        return anchor is not None and anchor >= recent_floor

    @staticmethod
    def _is_overdue_reminder(obj: CanonicalObject, now: datetime) -> bool:
        due_at = _as_utc(obj.due_at)
        return obj.source_record_type == "reminder" and due_at is not None and due_at < now

    @staticmethod
    def _is_upcoming(obj: CanonicalObject, now: datetime) -> bool:
        anchor = _as_utc(obj.start_at or obj.due_at)
        if anchor is None:
            return False
        return now <= anchor <= (now + timedelta(hours=24))

    @staticmethod
    def _resolve_domain_context(objects: Sequence[CanonicalObject]) -> str:
        if not objects:
            return "general"
        counts: Dict[str, int] = {}
        for obj in objects:
            domain = obj.domain.strip().lower() or "general"
            counts[domain] = counts.get(domain, 0) + 1
        return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
