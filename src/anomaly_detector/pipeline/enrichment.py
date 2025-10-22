"""Enrichment services for augmenting normalized events."""

from __future__ import annotations

import abc
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from anomaly_detector.pipeline.models import Event


@dataclass(slots=True)
class EnrichmentResult:
    event: Event
    metadata: Mapping[str, Any]


class Enricher(abc.ABC):
    """Base interface for enrichment providers."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abc.abstractmethod
    async def enrich(self, event: Event) -> EnrichmentResult:
        """Produce extra metadata for the given event."""


class CompositeEnricher(Enricher):
    """Chain multiple enrichers sequentially."""

    def __init__(self, enrichers: Sequence[Enricher]) -> None:
        super().__init__(name="composite")
        self._enrichers = list(enrichers)

    async def enrich(self, event: Event) -> EnrichmentResult:
        metadata: dict[str, Any] = {}
        for enricher in self._enrichers:
            result = await enricher.enrich(event)
            metadata[enricher.name] = result.metadata
        return EnrichmentResult(event=event, metadata=metadata)


class NoOpEnricher(Enricher):
    """Default enricher that returns the event without changes."""

    def __init__(self) -> None:
        super().__init__(name="noop")

    async def enrich(self, event: Event) -> EnrichmentResult:
        return EnrichmentResult(event=event, metadata={})


class GeoIPEnricher(Enricher):
    """Enrich events with GeoIP metadata using MaxMind databases."""

    def __init__(
        self,
        *,
        database_path: str | Path | None = None,
        reader: Any | None = None,
    ) -> None:
        super().__init__(name="geoip")
        self._reader = reader or self._load_reader(database_path)

    def _load_reader(self, database_path: str | Path | None) -> Any | None:
        if database_path is None:
            return None
        try:
            from geoip2.database import Reader
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "geoip2 package is required for GeoIP enrichment"
            ) from exc
        return Reader(str(database_path))

    async def enrich(self, event: Event) -> EnrichmentResult:
        metadata: dict[str, Any] = {}
        reader = self._reader
        ip = event.source_ip or event.destination_ip
        if reader is None or ip is None:
            return EnrichmentResult(event=event, metadata=metadata)

        try:
            record = reader.city(str(ip))
            metadata = {
                "country": getattr(record.country, "iso_code", None),
                "country_name": getattr(record.country, "name", None),
                "city": getattr(record.city, "name", None),
                "latitude": getattr(record.location, "latitude", None),
                "longitude": getattr(record.location, "longitude", None),
            }
        except Exception:  # pragma: no cover - depends on external db
            metadata = {}
        return EnrichmentResult(event=event, metadata={k: v for k, v in metadata.items() if v})


class ASNEnricher(Enricher):
    """Enrich events with Autonomous System metadata."""

    def __init__(
        self,
        *,
        database_path: str | Path | None = None,
        reader: Any | None = None,
    ) -> None:
        super().__init__(name="asn")
        self._reader = reader or self._load_reader(database_path)

    def _load_reader(self, database_path: str | Path | None) -> Any | None:
        if database_path is None:
            return None
        try:
            from geoip2.database import Reader
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "geoip2 package is required for ASN enrichment"
            ) from exc
        return Reader(str(database_path))

    async def enrich(self, event: Event) -> EnrichmentResult:
        reader = self._reader
        ip = event.source_ip or event.destination_ip
        metadata: dict[str, Any] = {}

        if reader is None or ip is None:
            return EnrichmentResult(event=event, metadata=metadata)

        try:
            record = reader.asn(str(ip))
            metadata = {
                "asn": getattr(record, "autonomous_system_number", None),
                "asn_org": getattr(record, "autonomous_system_organization", None),
            }
        except Exception:  # pragma: no cover - depends on external db
            metadata = {}
        return EnrichmentResult(event=event, metadata={k: v for k, v in metadata.items() if v})
