from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import TracebackType
from typing import Any, Callable, ContextManager, Dict, Optional, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class LayerMetric:
    layer: str
    action: str
    started_at: str
    ended_at: str
    elapsed_ms: int
    ok: bool
    details: Dict[str, Any]


class JsonlMetricsLogger:
    """Append-only local metrics logger (JSONL)."""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, metric: LayerMetric) -> None:
        line = json.dumps(
            {
                "layer": metric.layer,
                "action": metric.action,
                "started_at": metric.started_at,
                "ended_at": metric.ended_at,
                "elapsed_ms": metric.elapsed_ms,
                "ok": metric.ok,
                "details": metric.details,
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
        with self.path.open("a", encoding="utf-8") as file:
            file.write(line + "\n")

    def timed(
        self,
        *,
        layer: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> ContextManager[object]:
        logger = self
        details_map: Dict[str, Any] = dict(details or {})

        class _TimedContext:
            _start: float
            _started_at: datetime

            def __enter__(self_nonlocal) -> object:
                self_nonlocal._start = time.perf_counter()
                self_nonlocal._started_at = datetime.now(timezone.utc)
                return self_nonlocal

            def __exit__(
                self_nonlocal,
                exc_type: Optional[type[BaseException]],
                exc: Optional[BaseException],
                tb: Optional[TracebackType],
            ) -> None:
                ended_at = datetime.now(timezone.utc)
                elapsed_ms = int((time.perf_counter() - self_nonlocal._start) * 1000)
                logger.record(
                    LayerMetric(
                        layer=layer,
                        action=action,
                        started_at=self_nonlocal._started_at.isoformat(),
                        ended_at=ended_at.isoformat(),
                        elapsed_ms=elapsed_ms,
                        ok=exc is None,
                        details=details_map,
                    )
                )

        return _TimedContext()


def run_timed(
    logger: Optional[JsonlMetricsLogger],
    *,
    layer: str,
    action: str,
    fn: Callable[[], T],
    details: Optional[Dict[str, Any]] = None,
) -> T:
    if logger is None:
        return fn()

    started_at = datetime.now(timezone.utc)
    start_perf = time.perf_counter()
    ok = False
    try:
        result = fn()
        ok = True
        return result
    finally:
        ended_at = datetime.now(timezone.utc)
        elapsed_ms = int((time.perf_counter() - start_perf) * 1000)
        logger.record(
            LayerMetric(
                layer=layer,
                action=action,
                started_at=started_at.isoformat(),
                ended_at=ended_at.isoformat(),
                elapsed_ms=elapsed_ms,
                ok=ok,
                details=dict(details or {}),
            )
        )
