from datetime import datetime

from fastapi.testclient import TestClient

from anomaly_detector.api.main import app
from anomaly_detector.api.dependencies import get_anomaly_repository
from anomaly_detector.storage.repository import InMemoryAnomalyRepository
from anomaly_detector.pipeline.models import Event


def seed_repository() -> InMemoryAnomalyRepository:
    repo = InMemoryAnomalyRepository()
    repo.add(
        score=0.92,
        description="Suspicious SSH brute-force",
        event=Event(
            timestamp=datetime.utcnow(),
            source_ip=None,
            destination_ip=None,
            source_port=None,
            destination_port=None,
            protocol="ssh",
            payload={},
        ),
    )
    return repo


def test_list_anomalies_endpoint(monkeypatch) -> None:
    repo = seed_repository()
    monkeypatch.setattr("anomaly_detector.api.dependencies.get_anomaly_repository", lambda: repo)

    client = TestClient(app)
    response = client.get("/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["description"] == "Suspicious SSH brute-force"
