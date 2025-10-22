from datetime import datetime

import pytest

from anomaly_detector.metrics import ANOMALY_COUNTER, ANOMALY_SCORE_GAUGE
from anomaly_detector.pipeline.detection import PortScanHeuristicDetector
from anomaly_detector.pipeline.processor import PipelineProcessor


@pytest.mark.asyncio
async def test_metrics_increment_on_anomaly() -> None:
    ANOMALY_COUNTER.clear()
    ANOMALY_SCORE_GAUGE.clear()

    processor = PipelineProcessor(detector=PortScanHeuristicDetector())
    raw_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "src_ip": "192.168.0.10",
        "dst_ip": "192.168.0.11",
        "src_port": 12345,
        "dst_port": 22,
        "protocol": "tcp",
        "message": "failed login attempt",
    }

    result = await processor.process_raw_event(raw_event, collector="pytest")

    processed_value = ANOMALY_COUNTER.labels(type="processed")._value.get()
    anomaly_value = ANOMALY_COUNTER.labels(type="anomaly")._value.get()
    gauge_value = ANOMALY_SCORE_GAUGE.labels(detector=result.detector)._value.get()

    assert processed_value == 1.0
    assert anomaly_value == 1.0
    assert gauge_value >= 0.6
