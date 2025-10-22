"""Queue backend interfaces and utilities."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Iterable, Protocol

from anomaly_detector.config import get_settings

from anomaly_detector.pipeline.models import Event


class QueueSendError(Exception):
    """Raised when sending a batch to the queue fails."""


class QueueProducer(Protocol):
    """Protocol describing queue producers used by collectors."""

    async def send_batch(self, events: list[Event]) -> None:
        """Send a batch of events downstream."""


@dataclass(slots=True)
class QueueResult:
    """Result returned by queue producers after enqueueing."""

    count: int


class InMemoryQueueProducer:
    """Simple in-memory queue producer for testing and local development."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.events: list[Event] = []

    async def send_batch(self, events: list[Event]) -> None:
        async with self._lock:
            self.events.extend(events)

    def drain(self) -> Iterable[Event]:
        """Return and clear collected events."""

        events = list(self.events)
        self.events.clear()
        return events


class RedisQueueProducer:
    """Queue producer that writes events to a Redis stream."""

    def __init__(self, stream_name: str, max_retries: int = 3) -> None:
        from redis.asyncio import Redis  # lazy import to keep optional dependency handling simple

        settings = get_settings()
        self._stream = stream_name
        self._max_retries = max_retries
        self._redis = Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=False,
        )

    async def send_batch(self, events: list[Event]) -> None:
        if not events:
            return

        payloads = []
        for event in events:
            payloads.append(
                {
                    "timestamp": event.timestamp.isoformat(),
                    "source_ip": str(event.source_ip) if event.source_ip else "",
                    "destination_ip": str(event.destination_ip) if event.destination_ip else "",
                    "source_port": event.source_port or 0,
                    "destination_port": event.destination_port or 0,
                    "protocol": event.protocol or "",
                    "collector": event.collector or "",
                }
            )

        for attempt in range(1, self._max_retries + 1):
            try:
                await asyncio.gather(
                    *(self._redis.xadd(self._stream, data) for data in payloads)
                )
                return
            except Exception as exc:  # pragma: no cover - networking issues
                if attempt >= self._max_retries:
                    raise QueueSendError("Failed to send events to Redis stream") from exc
                await asyncio.sleep(0.1 * attempt)


class KafkaQueueProducer:
    """Queue producer that publishes events to a Kafka topic."""

    def __init__(self, topic: str, max_retries: int = 3) -> None:
        from aiokafka import AIOKafkaProducer  # lazy import to avoid hard dependency at import time

        settings = get_settings()
        self._topic = topic
        self._max_retries = max_retries
        self._producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap)
        self._startup_lock = asyncio.Lock()

    async def _ensure_started(self) -> None:
        if self._producer._closed:  # type: ignore[attr-defined]
            async with self._startup_lock:
                if self._producer._closed:  # type: ignore[attr-defined]
                    await self._producer.start()

    async def send_batch(self, events: list[Event]) -> None:
        if not events:
            return

        await self._ensure_started()

        payloads = []
        for event in events:
            payloads.append(
                {
                    "timestamp": event.timestamp.isoformat(),
                    "source_ip": str(event.source_ip) if event.source_ip else "",
                    "destination_ip": str(event.destination_ip) if event.destination_ip else "",
                    "source_port": event.source_port or 0,
                    "destination_port": event.destination_port or 0,
                    "protocol": event.protocol or "",
                    "collector": event.collector or "",
                }
            )

        for attempt in range(1, self._max_retries + 1):
            try:
                await asyncio.gather(
                    *(
                        self._producer.send_and_wait(self._topic, str(data).encode("utf-8"))
                        for data in payloads
                    )
                )
                return
            except Exception as exc:  # pragma: no cover - networking issues
                if attempt >= self._max_retries:
                    raise QueueSendError("Failed to send events to Kafka topic") from exc
                await asyncio.sleep(0.1 * attempt)

    async def close(self) -> None:
        if not self._producer._closed:  # type: ignore[attr-defined]
            await self._producer.stop()


def create_queue_producer() -> QueueProducer:
    settings = get_settings()
    backend = settings.queue_backend.lower()

    if backend == "redis":
        return RedisQueueProducer(
            stream_name=settings.queue_stream_name,
            max_retries=settings.queue_max_retries,
        )
    if backend == "memory":
        return InMemoryQueueProducer()
    if backend == "kafka":
        return KafkaQueueProducer(
            topic=settings.kafka_events_topic,
            max_retries=settings.queue_max_retries,
        )

    raise ValueError(f"Unsupported queue backend: {backend}")
