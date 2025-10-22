"""FastAPI application entrypoint."""

import asyncio
import json

from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from anomaly_detector.config import get_settings
from anomaly_detector.api.dependencies import get_anomaly_repository
from anomaly_detector.storage.repository import (
    AnomalyRecordModel,
    InMemoryAnomalyRepository,
)
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug)

cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if cors_origins != ["*"] else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Return basic application health information."""

    return {
        "status": "ok",
        "environment": settings.app_env,
        "version": "0.1.0",
    }


@app.get("/anomalies", tags=["anomalies"], response_model=list[AnomalyRecordModel])
async def list_anomalies(
    limit: int = 20,
    repository: InMemoryAnomalyRepository = Depends(get_anomaly_repository),
) -> list[AnomalyRecordModel]:
    """Return recent anomalies from the repository."""

    limit = max(1, min(limit, 200))
    return repository.list_recent_models(limit=limit)


@app.get("/metrics", tags=["system"])
async def metrics() -> Response:
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


async def _event_stream(repository: InMemoryAnomalyRepository, interval: float = 5.0):
    while True:
        anomalies = [record.model_dump(mode="json") for record in repository.list_recent_models(limit=50)]
        payload = json.dumps(anomalies)
        yield f"data: {payload}\n\n"
        await asyncio.sleep(interval)


@app.get("/events", tags=["anomalies"])
async def anomalies_event_stream(
    repository: InMemoryAnomalyRepository = Depends(get_anomaly_repository),
) -> StreamingResponse:
    return StreamingResponse(
        _event_stream(repository),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
