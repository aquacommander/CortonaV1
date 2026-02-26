"""Pipeline entry point for local ingestion and normalization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ingest.apple_notes import AppleNotesIngestor
from ingest.apple_reminders import AppleRemindersIngestor
from ingest.google_calendar import GoogleCalendarIngestor
from ingest.google_drive import GoogleDriveIngestor
from ingest.base import RawIngestResult
from normalize.canonical_event import normalize_raw_file


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest local personal data exports and normalize them into a "
            "canonical schema."
        )
    )
    parser.add_argument("--apple-notes-file", type=Path, help="Path to Apple Notes JSON export")
    parser.add_argument(
        "--apple-reminders-file",
        type=Path,
        help="Path to Apple Reminders JSON export",
    )
    parser.add_argument(
        "--google-calendar-file",
        type=Path,
        help="Path to Google Calendar JSON export",
    )
    parser.add_argument(
        "--google-drive-dir",
        type=Path,
        help=(
            "Path to a local Google Drive directory (synced/exported). "
            "Ingestion captures file metadata only."
        ),
    )
    parser.add_argument(
        "--google-drive-checksum",
        action="store_true",
        help="Compute SHA-256 for Google Drive files (slower on large folders).",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Root of local-ingest project (defaults to current script directory)",
    )
    return parser.parse_args()


def _require_existing_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")


def _require_existing_dir(path: Path) -> None:
    if not path.exists() or not path.is_dir():
        raise NotADirectoryError(f"Input directory not found: {path}")


def run_pipeline(args: argparse.Namespace) -> None:
    project_root = args.project_root.resolve()
    raw_dir = project_root / "storage" / "raw"
    normalized_dir = project_root / "storage" / "normalized"

    file_ingestors = [
        (args.apple_notes_file, AppleNotesIngestor()),
        (args.apple_reminders_file, AppleRemindersIngestor()),
        (args.google_calendar_file, GoogleCalendarIngestor()),
    ]

    raw_results: list[RawIngestResult] = []
    for source_file, ingestor in file_ingestors:
        if source_file is None:
            continue
        source_file = source_file.resolve()
        _require_existing_file(source_file)
        result = ingestor.ingest(source_file=source_file, raw_output_dir=raw_dir)
        raw_results.append(result)
        print(f"[ingest] {result.source}: {result.raw_output_file}")

    if args.google_drive_dir is not None:
        source_dir = args.google_drive_dir.resolve()
        _require_existing_dir(source_dir)
        google_drive_ingestor = GoogleDriveIngestor(
            include_checksum=args.google_drive_checksum
        )
        result = google_drive_ingestor.ingest(
            source_file=source_dir,
            raw_output_dir=raw_dir,
        )
        raw_results.append(result)
        print(f"[ingest] {result.source}: {result.raw_output_file}")

    if not raw_results:
        print("[ingest] No source files were provided. Skipping normalization.")
        return

    combined_records = []
    for result in raw_results:
        normalized_file = normalize_raw_file(
            raw_file_path=result.raw_output_file,
            normalized_output_dir=normalized_dir,
        )
        print(f"[normalize] {result.source}: {normalized_file}")

        with normalized_file.open("r", encoding="utf-8") as handle:
            combined_records.extend(json.load(handle))

    combined_records.sort(key=lambda item: item["canonical_id"])
    combined_output = normalized_dir / "canonical_all.json"
    with combined_output.open("w", encoding="utf-8") as handle:
        json.dump(combined_records, handle, indent=2, ensure_ascii=False)
    print(f"[normalize] combined: {combined_output}")


if __name__ == "__main__":
    run_pipeline(_parse_args())
