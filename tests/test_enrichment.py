import types

import pytest

from anomaly_detector.pipeline.enrichment import (
    ASNEnricher,
    CompositeEnricher,
    EnrichmentResult,
    GeoIPEnricher,
    NoOpEnricher,
)
from anomaly_detector.pipeline.models import Event
from datetime import datetime


def make_event():
    return Event(
        timestamp=datetime.utcnow(),
        source_ip=None,
        destination_ip=None,
        source_port=None,
        destination_port=None,
        protocol="tcp",
        payload={},
    )


@pytest.mark.asyncio
async def test_geoip_enricher_adds_metadata():
    class DummyGeoReader:
        def city(self, ip):  # noqa: D401
            return types.SimpleNamespace(
                country=types.SimpleNamespace(iso_code="TR", name="Turkey"),
                city=types.SimpleNamespace(name="Istanbul"),
                location=types.SimpleNamespace(latitude=41.0, longitude=29.0),
            )

    event = make_event()
    event.destination_ip = type("IP", (), {"__str__": lambda self: "8.8.8.8"})()

    enricher = GeoIPEnricher(reader=DummyGeoReader())
    result = await enricher.enrich(event)
    assert isinstance(result, EnrichmentResult)
    assert result.metadata["country"] == "TR"
    assert result.metadata["city"] == "Istanbul"


@pytest.mark.asyncio
async def test_asn_enricher_adds_metadata():
    class DummyASNReader:
        def asn(self, ip):
            return types.SimpleNamespace(
                autonomous_system_number=15169,
                autonomous_system_organization="Google LLC",
            )

    event = make_event()
    event.source_ip = type("IP", (), {"__str__": lambda self: "1.1.1.1"})()

    enricher = ASNEnricher(reader=DummyASNReader())
    result = await enricher.enrich(event)
    assert result.metadata["asn"] == 15169
    assert result.metadata["asn_org"] == "Google LLC"


@pytest.mark.asyncio
async def test_composite_enricher_chains_results():
    class StaticEnricher(NoOpEnricher):
        def __init__(self, name, data):
            super().__init__()
            self.name = name
            self.data = data

        async def enrich(self, event: Event) -> EnrichmentResult:  # type: ignore[override]
            return EnrichmentResult(event=event, metadata=self.data)

    event = make_event()
    composite = CompositeEnricher(
        [StaticEnricher("one", {"value": 1}), StaticEnricher("two", {"value": 2})]
    )

    result = await composite.enrich(event)
    assert set(result.metadata.keys()) == {"one", "two"}
