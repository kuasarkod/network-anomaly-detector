from __future__ import annotations

from datetime import datetime
from ipaddress import IPv4Address

import pytest

from anomaly_detector.collectors.base import Collector, CollectorConfig, CollectorContext
from anomaly_detector.pipeline.models import Event
from anomaly_detector.pipeline.queue import InMemoryQueueProducer


class SimpleCollector(Collector):
    def __init__(self, config: CollectorConfig, batches: list[list[Event]], queue: InMemoryQueueProducer):
        super().__init__(config)
        self._batches = batches
        self._queue = queue

    async def iter_batches(self, context: CollectorContext):
        for batch in self._batches:
            yield batch

    async def handle_batch(self, batch: list[Event], context: CollectorContext) -> None:
        await self._queue.send_batch(batch)


@pytest.mark.asyncio
async def test_collector_sends_events_to_queue() -> None:
    queue = InMemoryQueueProducer()
    config = CollectorConfig(name="simple", batch_size=2)
    context = CollectorContext(name="simple", source="test", extra={})

    batch1 = [
        Event(
            timestamp=datetime.utcnow(),
            source_ip=IPv4Address("192.168.1.10"),
            destination_ip=IPv4Address("192.168.1.20"),
            source_port=12345,
            destination_port=22,
            protocol="tcp",
            payload={"message": "ssh login attempt"},
            collector="simple",
        ),
    ]

    batch2 = [
        Event(
            timestamp=datetime.utcnow(),
            source_ip=IPv4Address("10.0.0.5"),
            destination_ip=IPv4Address("10.0.0.8"),
            source_port=443,
            destination_port=51515,
            protocol="udp",
            payload={"message": "dns response"},
            collector="simple",
        ),
        Event(
            timestamp=datetime.utcnow(),
            source_ip=None,
            destination_ip=None,
            source_port=None,
            destination_port=None,
            protocol="syslog",
            payload={"message": "system reboot"},
            collector="simple",
        ),
    ]

    collector = SimpleCollector(config=config, batches=[batch1, batch2], queue=queue)

    await collector.run(context)

    drained = list(queue.drain())
    assert len(drained) == 3
    protocols = {event.protocol for event in drained}
    assert protocols == {"tcp", "udp", "syslog"}
