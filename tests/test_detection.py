from datetime import datetime

import pytest

from anomaly_detector.pipeline.detection import (
    DetectionResult,
    IsolationForestDetector,
    PortScanHeuristicDetector,
)
from anomaly_detector.pipeline.models import Event


def make_event(**overrides):
    base = dict(
        timestamp=datetime.utcnow(),
        source_ip=None,
        destination_ip=None,
        source_port=None,
        destination_port=None,
        protocol=None,
        payload={},
    )
    base.update(overrides)
    return Event(**base)


def test_port_scan_detector_flags_sensitive_port():
    event = make_event(destination_port=22, protocol="tcp")
    detector = PortScanHeuristicDetector()
    result = detector.evaluate(event)
    assert isinstance(result, DetectionResult)
    assert result.is_anomaly
    assert result.score >= 0.6
    assert result.description == "Sensitive service targeted"


def test_port_scan_detector_handles_non_sensitive():
    event = make_event(destination_port=8080, protocol="http")
    detector = PortScanHeuristicDetector()
    result = detector.evaluate(event)
    assert not result.is_anomaly
    assert result.score == 0.0


def generate_training_events(count: int = 20):
    events = []
    for i in range(count):
        events.append(
            make_event(
                source_port=1000 + i,
                destination_port=80,
                protocol="http",
                payload={"size": 1},
            )
        )
    return events


def test_isolation_forest_requires_fit():
    detector = IsolationForestDetector(contamination=0.2, random_state=1)
    event = make_event(destination_port=80, protocol="http")
    with pytest.raises(RuntimeError):
        detector.evaluate(event)


def test_isolation_forest_detects_outlier():
    detector = IsolationForestDetector(contamination=0.2, random_state=1)
    normal_events = generate_training_events()
    detector.fit(normal_events)

    outlier = make_event(
        source_port=55555,
        destination_port=23,
        protocol="tcp",
        payload={"failed": True, "size": 20},
    )

    result = detector.evaluate(outlier)
    assert isinstance(result, DetectionResult)
    assert result.score >= 0.5
    assert result.is_anomaly
