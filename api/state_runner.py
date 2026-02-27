from __future__ import annotations

from state.engine import DeterministicStateEngine, StateEngineConfig
from state.models import UserStateSnapshot
from storage.sqlite_store import SQLiteStore


def compute_user_state(
    *,
    db_path: str,
    recent_window_days: int = 7,
    follow_up_window_days: int = 7,
) -> UserStateSnapshot:
    store = SQLiteStore(db_path)
    engine = DeterministicStateEngine(
        StateEngineConfig(
            recent_window_days=recent_window_days,
            follow_up_window_days=follow_up_window_days,
        )
    )
    return engine.calculate_from_store(store)
