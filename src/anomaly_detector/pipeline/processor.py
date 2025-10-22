"""Orchestrates normalization, enrichment, detection and alerting."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from anomaly_detector.alerts.base import Alert, AlertDispatcher
from anomaly_detector.pipeline.detection import Detector, DetectionResult
from anomaly_detector.pipeline.enrichment import (
    ASNEnricher,
    CompositeEnricher,
    Enricher,
    GeoIPEnricher,
    NoOpEnricher,
)
from anomaly_detector.pipeline.models import Event
from anomaly_detector.pipeline.normalization import EventNormalizer
from anomaly_detector.storage.repository import InMemoryAnomalyRepository
from anomaly_detector.metrics import record_event, record_score
from anomaly_detector.config import get_settings


class PipelineProcessor:
    """Process raw telemetry through the detection pipeline."""

    def __init__(
        self,
        *,
        normalizer: Optional[EventNormalizer] = None,
        detector: Optional[Detector] = None,
        enricher: Optional[Enricher] = None,
        repository: Optional[InMemoryAnomalyRepository] = None,
        dispatcher: Optional[AlertDispatcher] = None,
        anomaly_threshold: float = 0.5,
    ) -> None:
        self.normalizer = normalizer or EventNormalizer()
        self.detector = detector
        if enricher is not None:
            self.enricher = enricher
        else:
            settings = get_settings()
            enricher_chain: list[Enricher] = []
            if settings.geoip_db_path:
                enricher_chain.append(GeoIPEnricher(database_path=settings.geoip_db_path))
            if settings.asn_db_path:
                enricher_chain.append(ASNEnricher(database_path=settings.asn_db_path))
            if enricher_chain:
                if len(enricher_chain) == 1:
                    self.enricher = enricher_chain[0]
                else:
                    self.enricher = CompositeEnricher(enricher_chain)
            else:
                self.enricher = NoOpEnricher()
        self.repository = repository or InMemoryAnomalyRepository()
        self.dispatcher = dispatcher
        self.anomaly_threshold = anomaly_threshold

    async def process_raw_event(
        self, raw_event: Mapping[str, Any], *, collector: str | None = None
    ) -> DetectionResult:
        """Normalize, enrich, detect and optionally alert on a raw event."""

        normalization = self.normalizer.normalize(raw_event, collector=collector)
        event = normalization.event
        record_event("processed")

        enrichment = await self.enricher.enrich(event)
        if enrichment.metadata:
            enriched_payload = dict(event.payload)
            enriched_payload["enrichment"] = enrichment.metadata
            event.payload = enriched_payload

        if self.detector is None:
            detection = DetectionResult(
                event=event,
                score=0.0,
                detector="none",
            )
        else:
            detection = self.detector.evaluate(event)

        record_score(detection.detector, detection.score)

        if detection.score >= self.anomaly_threshold:
            event.add_tag("anomaly")
            record_event("anomaly")
            record = self.repository.add(
                score=detection.score,
                description=detection.description,
                event=event,
            )
            if self.dispatcher is not None:
                alert = self._build_alert(record.event, detection)
                await self.dispatcher.dispatch(alert)

        return detection

    def _build_alert(self, event: Event, detection: DetectionResult) -> Alert:
        severity = self._severity_from_score(detection.score)
        title = f"Anomaly detected by {detection.detector}"
        metadata = {
            "score": f"{detection.score:.2f}",
            "description": detection.description,
            "source_ip": str(event.source_ip or "unknown"),
            "destination_ip": str(event.destination_ip or "unknown"),
        }
        return Alert(
            title=title,
            severity=severity,
            event=event,
            metadata=metadata,
        )

    @staticmethod
    def _severity_from_score(score: float) -> str:
        if score >= 0.85:
            return "critical"
        if score >= 0.6:
            return "high"
        return "medium"
