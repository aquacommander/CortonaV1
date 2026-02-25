"""Ingest Apple Reminders exports into storage/raw."""

from __future__ import annotations

from pathlib import Path

from .base import BaseIngestor, RawIngestResult


class AppleRemindersIngestor(BaseIngestor):
    """Reads Apple Reminders JSON exports without modification."""

    source_name = "apple_reminders"

    def ingest(self, source_file: Path, raw_output_dir: Path) -> RawIngestResult:
        payload = self.read_json_file(source_file)
        return self.write_raw_snapshot(payload, source_file, raw_output_dir)
