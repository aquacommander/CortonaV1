"""Shared ingestion primitives for local data sources.

The ingestion layer has one responsibility: copy source exports into
`storage/raw/` without transformation. Any interpretation happens later in
the normalization layer.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RawIngestResult:
    """Metadata about a raw ingestion write."""

    source: str
    source_file: Path
    raw_output_file: Path


class BaseIngestor(ABC):
    """Base class for deterministic local ingestors."""

    source_name: str

    @abstractmethod
    def ingest(self, source_file: Path, raw_output_dir: Path) -> RawIngestResult:
        """Read a source export and write an untouched raw snapshot."""

    def read_json_file(self, source_file: Path) -> Any:
        """Read JSON payload from disk.

        We intentionally do not clean or coerce values here.
        """
        with source_file.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def write_raw_snapshot(
        self,
        payload: Any,
        source_file: Path,
        raw_output_dir: Path,
    ) -> RawIngestResult:
        """Write raw payload and minimal lineage metadata to storage/raw."""
        raw_output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_file = raw_output_dir / f"{self.source_name}_{timestamp}.json"

        snapshot = {
            "source": self.source_name,
            "source_file": str(source_file),
            "ingested_at_utc": timestamp,
            "payload": payload,
        }

        with output_file.open("w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, indent=2, ensure_ascii=False)

        return RawIngestResult(
            source=self.source_name,
            source_file=source_file,
            raw_output_file=output_file,
        )
