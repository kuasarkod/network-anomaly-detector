"""Command-line interface for the anomaly detector service."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from anomaly_detector.pipeline.detection import PortScanHeuristicDetector
from anomaly_detector.pipeline.processor import PipelineProcessor
from anomaly_detector.alerts.base import AlertDispatcher
from anomaly_detector.pipeline.enrichment import NoOpEnricher
from anomaly_detector.api.dependencies import get_anomaly_repository


def load_events_from_file(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if isinstance(data, list):
        return data
    raise ValueError("Input file must contain a JSON array of events")


async def run_file_ingest(path: Path) -> None:
    events = load_events_from_file(path)
    repository = get_anomaly_repository()
    dispatcher = AlertDispatcher([])
    processor = PipelineProcessor(
        detector=PortScanHeuristicDetector(),
        dispatcher=dispatcher,
        repository=repository,
        enricher=NoOpEnricher(),
    )

    for event in events:
        await processor.process_raw_event(event, collector="cli")

    print(f"Processed {len(events)} events. Stored anomalies: {len(repository.list_recent_models())}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Anomaly detector CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest events from JSON file")
    ingest_parser.add_argument("path", type=Path, help="Path to JSON lines or array file")

    subparsers.add_parser("stats", help="Show repository statistics")

    return parser


async def main_async(args: argparse.Namespace) -> None:
    if args.command == "ingest":
        await run_file_ingest(args.path)
    elif args.command == "stats":
        repository = get_anomaly_repository()
        anomalies = repository.list_recent_models()
        print(json.dumps([record.dict() for record in anomalies], default=str, indent=2))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
