"""Ingest Google Calendar exports into storage/raw."""

from __future__ import annotations

from pathlib import Path

from .base import BaseIngestor, RawIngestResult


class GoogleCalendarIngestor(BaseIngestor):
    """Reads Google Calendar JSON exports without modification."""

    source_name = "google_calendar"

    def ingest(self, source_file: Path, raw_output_dir: Path) -> RawIngestResult:
        payload = self.read_json_file(source_file)
        return self.write_raw_snapshot(payload, source_file, raw_output_dir)
