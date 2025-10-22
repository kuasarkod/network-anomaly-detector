"""Anomaly detection engine primitives."""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
from sklearn.ensemble import IsolationForest

from anomaly_detector.pipeline.models import Event


@dataclass(slots=True)
class DetectionResult:
    event: Event
    score: float
    description: str
    detector: str

    @property
    def is_anomaly(self) -> bool:
        return self.score >= 0.5


class Detector(abc.ABC):
    """Base interface for anomaly detectors."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abc.abstractmethod
    def evaluate(self, event: Event) -> DetectionResult:
        """Score a single event and return a detection result."""


class CompositeDetector(Detector):
    """Aggregate multiple detectors and choose the highest score."""

    def __init__(self, detectors: Sequence[Detector]) -> None:
        super().__init__(name="composite")
        self._detectors = list(detectors)

    def evaluate(self, event: Event) -> DetectionResult:
        results = [detector.evaluate(event) for detector in self._detectors]
        best = max(results, key=lambda result: result.score, default=None)
        if best is None:
            return DetectionResult(event=event, score=0.0, description="no detectors", detector="none")
        return best


class PortScanHeuristicDetector(Detector):
    """Simple heuristic that flags repeated port access patterns."""

    def __init__(self, *, sensitive_ports: Iterable[int] | None = None) -> None:
        super().__init__(name="port-scan-heuristic")
        self._sensitive_ports = set(sensitive_ports or {22, 23, 3389, 5900})

    def evaluate(self, event: Event) -> DetectionResult:
        score = 0.0
        description = "benign"

        if event.destination_port in self._sensitive_ports and event.protocol in {"tcp", "udp", "ssh"}:
            score += 0.6
            description = "Sensitive service targeted"

        if event.source_ip and event.destination_ip and event.source_ip == event.destination_ip:
            score += 0.2
            description = "Loopback access to sensitive port"

        if "failed" in (event.payload.get("message", "").lower() if event.payload else ""):
            score += 0.2
            description = "Repeated failure on sensitive port"

        score = min(score, 1.0)
        return DetectionResult(event=event, score=score, description=description, detector=self.name)


def _event_to_vector(event: Event) -> np.ndarray:
    """Convert an event into a numeric feature vector for ML detectors."""

    src_port = event.source_port or 0
    dst_port = event.destination_port or 0
    protocol_map = {"tcp": 1, "udp": 2, "icmp": 3, "http": 4, "https": 5, "ssh": 6}
    protocol_value = protocol_map.get((event.protocol or "").lower(), 0)
    payload_size = len(event.payload or {})
    tags_count = len(event.tags)
    return np.array([src_port, dst_port, protocol_value, payload_size, tags_count], dtype=float)


class IsolationForestDetector(Detector):
    """IsolationForest-based anomaly detector for structured network events."""

    def __init__(
        self,
        *,
        contamination: float = 0.1,
        random_state: int | None = 42,
        warm_start: bool = False,
    ) -> None:
        super().__init__(name="isolation-forest")
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            warm_start=warm_start,
        )
        self._fitted = False

    def fit(self, events: Iterable[Event]) -> None:
        vectors = np.vstack([_event_to_vector(event) for event in events])
        self.model.fit(vectors)
        self._fitted = True

    def evaluate(self, event: Event) -> DetectionResult:
        if not self._fitted:
            raise RuntimeError("IsolationForestDetector must be fitted before evaluation")

        vector = _event_to_vector(event).reshape(1, -1)
        score = -self.model.decision_function(vector)[0]
        normalized = float((score + 1) / 2)
        description = "IsolationForest anomaly" if normalized >= 0.5 else "IsolationForest benign"
        return DetectionResult(
            event=event,
            score=min(max(normalized, 0.0), 1.0),
            description=description,
            detector=self.name,
        )
