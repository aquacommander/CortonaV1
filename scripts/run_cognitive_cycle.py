from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from api.cycle_runner import run_cognitive_cycle_from_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the full local-first Cortona cognitive cycle."
    )
    parser.add_argument("--notes", required=True, help="Path to Apple Notes JSON export.")
    parser.add_argument("--calendar", required=True, help="Path to Google Calendar JSON export.")
    parser.add_argument("--reminders", required=True, help="Path to Apple Reminders JSON export.")
    parser.add_argument("--db", default="data/cortona.db", help="SQLite database output path.")
    parser.add_argument("--index", default="data/memory.faiss", help="FAISS index output path.")
    parser.add_argument(
        "--metadata",
        default="data/memory.meta.json",
        help="Embedding metadata JSON output path.",
    )
    parser.add_argument(
        "--metrics",
        default="data/metrics.jsonl",
        help="Metrics JSONL output path.",
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip embedding rebuild even if dependencies are installed.",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Restrict embedding model loading to local cache only.",
    )
    parser.add_argument(
        "--embedding-model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Local sentence-transformers model name for embedding rebuild.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = run_cognitive_cycle_from_files(
        notes_path=args.notes,
        calendar_path=args.calendar,
        reminders_path=args.reminders,
        db_path=args.db,
        index_path=args.index,
        metadata_path=args.metadata,
        metrics_path=args.metrics,
        rebuild_embeddings=not args.skip_embeddings,
        embeddings_model_name=args.embedding_model,
        local_files_only=args.local_files_only,
    )
    print(json.dumps(asdict(report), indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
