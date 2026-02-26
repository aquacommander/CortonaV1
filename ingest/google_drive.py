"""Ingest local Google Drive folders into storage/raw.

This ingestor is local-first by design. It scans an already-synced or exported
directory and captures deterministic file metadata without modifying files.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base import BaseIngestor, RawIngestResult


def _to_utc_iso(timestamp: float) -> str:
    """Convert POSIX timestamp into UTC ISO-8601 string."""
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )


class GoogleDriveIngestor(BaseIngestor):
    """Reads local Google Drive files and writes raw metadata snapshot."""

    source_name = "google_drive"

    def __init__(self, include_checksum: bool = False) -> None:
        self.include_checksum = include_checksum

    def _sha256(self, file_path: Path) -> str:
        digest = hashlib.sha256()
        with file_path.open("rb") as handle:
            while True:
                block = handle.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
        return digest.hexdigest()

    def _file_record(self, root_dir: Path, file_path: Path) -> dict[str, Any]:
        stat = file_path.stat()
        record: dict[str, Any] = {
            "file_name": file_path.name,
            "relative_path": str(file_path.relative_to(root_dir)).replace("\\", "/"),
            "absolute_path": str(file_path.resolve()),
            "extension": file_path.suffix.lower(),
            "size_bytes": stat.st_size,
            "created_at": _to_utc_iso(stat.st_ctime),
            "updated_at": _to_utc_iso(stat.st_mtime),
        }
        if self.include_checksum:
            record["sha256"] = self._sha256(file_path)
        return record

    def ingest(self, source_file: Path, raw_output_dir: Path) -> RawIngestResult:
        """Scan directory and write file metadata as raw payload.

        The base interface uses `source_file` naming, but for this ingestor
        the path is expected to be a directory.
        """
        root_dir = source_file
        payload_files: list[dict[str, Any]] = []
        for file_path in sorted(root_dir.rglob("*")):
            if not file_path.is_file():
                continue
            payload_files.append(self._file_record(root_dir, file_path))

        payload = {
            "root_dir": str(root_dir.resolve()),
            "files": payload_files,
            "file_count": len(payload_files),
            "include_checksum": self.include_checksum,
        }
        return self.write_raw_snapshot(payload, root_dir, raw_output_dir)
