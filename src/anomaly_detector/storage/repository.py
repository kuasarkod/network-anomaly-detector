"""Storage abstractions for anomaly records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List

from pydantic import BaseModel

from anomaly_detector.pipeline.models import Event


@dataclass(slots=True)
class AnomalyRecord:
    id: int
    detected_at: datetime
    score: float
    description: str
    event: Event


class InMemoryAnomalyRepository:
    """Simple repository storing anomalies in memory for prototyping."""

    def __init__(self) -> None:
        self._items: List[AnomalyRecord] = []
        self._counter: int = 0

    def add(self, *, score: float, description: str, event: Event) -> AnomalyRecord:
        self._counter += 1
        record = AnomalyRecord(
            id=self._counter,
            detected_at=datetime.utcnow(),
            score=score,
            description=description,
            event=event,
        )
        self._items.append(record)
        return record

    def list_recent(self, limit: int = 50) -> Iterable[AnomalyRecord]:
        return list(reversed(self._items))[:limit]

    def clear(self) -> None:
        self._items.clear()
        self._counter = 0

    def list_recent_models(self, limit: int = 50) -> list[AnomalyRecordModel]:
        return [AnomalyRecordModel(**record.__dict__) for record in self.list_recent(limit)]


class AnomalyRecordModel(BaseModel):
    id: int
    detected_at: datetime
    score: float
    description: str
    event: Event

    class Config:
        arbitrary_types_allowed = True
