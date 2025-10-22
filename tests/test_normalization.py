from datetime import datetime

import pytest

from anomaly_detector.pipeline.normalization import EventNormalizer, NormalizationError


def test_normalizer_success() -> None:
    normalizer = EventNormalizer()
    raw = {
        "timestamp": datetime.utcnow().isoformat(),
        "src_ip": "192.168.1.1",
        "dst_ip": "192.168.1.2",
        "src_port": "1234",
        "dst_port": 80,
        "protocol": "TCP",
        "message": "Example log entry",
    }

    result = normalizer.normalize(raw, collector="syslog")

    assert result.event.source_ip and str(result.event.source_ip) == "192.168.1.1"
    assert result.event.destination_port == 80
    assert result.event.protocol == "tcp"
    assert result.event.collector == "syslog"


def test_normalizer_missing_timestamp() -> None:
    normalizer = EventNormalizer()
    raw = {"src_ip": "10.0.0.1"}

    with pytest.raises(NormalizationError):
        normalizer.normalize(raw)


def test_normalizer_invalid_ip() -> None:
    normalizer = EventNormalizer()
    raw = {
        "timestamp": datetime.utcnow().isoformat(),
        "src_ip": "invalid-ip",
    }

    with pytest.raises(NormalizationError):
        normalizer.normalize(raw)
