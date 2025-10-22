"""Prometheus metrics instrumentation."""

from __future__ import annotations

from prometheus_client import Counter, Gauge

ANOMALY_COUNTER = Counter(
    "anomaly_detector_events_total",
    "Total number of events processed by the anomaly detector",
    labelnames=("type",),
)

ANOMALY_SCORE_GAUGE = Gauge(
    "anomaly_detector_last_score",
    "Score of the most recent anomaly detection",
    labelnames=("detector",),
)


def record_event(event_type: str) -> None:
    ANOMALY_COUNTER.labels(type=event_type).inc()


def record_score(detector: str, score: float) -> None:
    ANOMALY_SCORE_GAUGE.labels(detector=detector).set(score)
