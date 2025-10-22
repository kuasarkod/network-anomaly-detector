import asyncio
from datetime import datetime

import pytest

from anomaly_detector.alerts.base import Alert, AlertChannel
from anomaly_detector.pipeline.detection import PortScanHeuristicDetector
from anomaly_detector.pipeline.processor import PipelineProcessor
from anomaly_detector.pipeline.models import Event


class DummyChannel(AlertChannel):
    def __init__(self) -> None:
        super().__init__(name="dummy")
        self.alerts: list[Alert] = []

    async def send(self, alert: Alert) -> None:
        self.alerts.append(alert)


@pytest.mark.asyncio
async def test_pipeline_processor_detects_and_alerts():
    channel = DummyChannel()
    processor = PipelineProcessor(
        detector=PortScanHeuristicDetector(),
        dispatcher=channel,
    )

    raw_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "dst_ip": "10.0.0.1",
        "dst_port": 22,
        "protocol": "tcp",
        "message": "failed login attempt",
    }

    result = await processor.process_raw_event(raw_event, collector="syslog")

    assert result.is_anomaly
    assert len(channel.alerts) == 1
    assert channel.alerts[0].metadata["description"] == "Sensitive service targeted"
    repo_events = processor.repository.list_recent_models()
    assert len(repo_events) == 1
