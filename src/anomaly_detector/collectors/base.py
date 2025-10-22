"""Collector interface and shared utilities."""

from __future__ import annotations

import abc
import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional

from anomaly_detector.pipeline.models import Event


@dataclass(slots=True)
class CollectorContext:
    """Context data shared with collectors at runtime."""

    name: str
    source: str
    extra: dict[str, Any]


@dataclass(slots=True)
class CollectorConfig:
    """Minimal configuration required by collectors."""

    name: str
    batch_size: int = 100
    flush_interval: float = 1.0  # seconds
    enabled: bool = True


class Collector(abc.ABC):
    """Abstract collector definition."""

    def __init__(self, config: CollectorConfig):
        self.config = config
        self._shutdown_event = asyncio.Event()

    @property
    def name(self) -> str:
        return self.config.name

    async def run(self, context: CollectorContext) -> None:
        """Run the collector until shutdown."""

        if not self.config.enabled:
            return

        async for batch in self.iter_batches(context):
            await self.handle_batch(batch, context)
            if self._shutdown_event.is_set():
                break

    async def shutdown(self) -> None:
        """Signal the collector to stop."""

        self._shutdown_event.set()

    @abc.abstractmethod
    async def iter_batches(self, context: CollectorContext) -> AsyncIterator[list[Event]]:
        """Yield batches of events produced by the collector."""

    @abc.abstractmethod
    async def handle_batch(self, batch: list[Event], context: CollectorContext) -> None:
        """Deliver collected events (e.g. push to queue)."""

    async def wait_for_shutdown(self, timeout: Optional[float] = None) -> None:
        try:
            await asyncio.wait_for(self._shutdown_event.wait(), timeout)
        except asyncio.TimeoutError:
            pass
