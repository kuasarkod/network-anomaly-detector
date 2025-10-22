"""FastAPI dependency utilities."""

from __future__ import annotations

from functools import lru_cache

from anomaly_detector.storage.repository import InMemoryAnomalyRepository


@lru_cache()
def get_anomaly_repository() -> InMemoryAnomalyRepository:
    return InMemoryAnomalyRepository()
