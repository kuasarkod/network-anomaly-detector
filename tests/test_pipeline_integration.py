from datetime import datetime, timedelta

import pytest

from anomaly_detector.collectors.base import Collector, CollectorConfig, CollectorContext
from anomaly_detector.pipeline.models import Event
from anomaly_detector.pipeline.normalization import EventNormalizer
from anomaly_detector.pipeline.queue import InMemoryQueueProducer


class NormalizingCollector(Collector):
    def __init__(self, config: CollectorConfig, raw_batches, queue: InMemoryQueueProducer):
        super().__init__(config)
        self._raw_batches = raw_batches
        self._queue = queue
        self._normalizer = EventNormalizer()

    async def iter_batches(self, context: CollectorContext):
        for raw_batch in self._raw_batches:
            normalized = []
            for raw in raw_batch:
                result = self._normalizer.normalize(raw, collector=context.name)
                normalized.append(result.event)
            yield normalized

    async def handle_batch(self, batch: list[Event], context: CollectorContext) -> None:
        await self._queue.send_batch(batch)


@pytest.mark.asyncio
async def test_pipeline_normalizes_and_delivers_events() -> None:
    queue = InMemoryQueueProducer()
    config = CollectorConfig(name="syslog", batch_size=2)
    context = CollectorContext(name="syslog", source="fixture", extra={})

    now = datetime.utcnow()
    raw_batches = [
        [
            {
                "timestamp": (now - timedelta(seconds=1)).isoformat(),
                "src_ip": "192.168.10.21",
                "dst_ip": "192.168.10.1",
                "src_port": 51514,
                "dst_port": 514,
                "protocol": "syslog",
                "message": "Accepted password for user",
            },
            {
                "timestamp": now.isoformat(),
                "src_ip": "192.168.10.30",
                "dst_ip": "192.168.10.2",
                "src_port": 443,
                "dst_port": 51515,
                "protocol": "https",
                "status": 200,
            },
        ]
    ]

    collector = NormalizingCollector(config=config, raw_batches=raw_batches, queue=queue)
    await collector.run(context)

    events = list(queue.drain())
    assert len(events) == 2
    assert events[0].protocol == "syslog"
    assert events[1].payload["status"] == 200
    assert events[0].collector == "syslog"
