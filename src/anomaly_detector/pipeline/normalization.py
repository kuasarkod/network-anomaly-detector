"""Utilities for normalizing raw telemetry into canonical events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from ipaddress import ip_address
from typing import Any, Mapping, MutableMapping, Optional

from anomaly_detector.pipeline.models import Event, IPAddress


class NormalizationError(Exception):
    """Raised when a payload cannot be normalized."""


@dataclass(slots=True)
class NormalizationResult:
    event: Event
    discarded_fields: dict[str, Any]


class EventNormalizer:
    """Simple normalizer converting raw dictionaries into `Event` objects."""

    TIMESTAMP_KEYS = ("timestamp", "time", "@timestamp")
    SOURCE_IP_KEYS = ("src_ip", "source_ip", "client_ip")
    DEST_IP_KEYS = ("dst_ip", "destination_ip", "server_ip")
    SOURCE_PORT_KEYS = ("src_port", "source_port")
    DEST_PORT_KEYS = ("dst_port", "destination_port")
    PROTOCOL_KEYS = ("protocol", "proto")

    def __init__(self, *, allow_missing_ip: bool = True) -> None:
        self.allow_missing_ip = allow_missing_ip

    def normalize(self, raw: Mapping[str, Any], *, collector: str | None = None) -> NormalizationResult:
        payload = dict(raw)
        timestamp = self._extract_timestamp(payload)
        src_ip = self._extract_ip(payload, self.SOURCE_IP_KEYS)
        dst_ip = self._extract_ip(payload, self.DEST_IP_KEYS)
        src_port = self._extract_int(payload, self.SOURCE_PORT_KEYS)
        dst_port = self._extract_int(payload, self.DEST_PORT_KEYS)
        protocol = self._extract_str(payload, self.PROTOCOL_KEYS)

        if not self.allow_missing_ip and (src_ip is None and dst_ip is None):
            raise NormalizationError("Missing both source and destination IP addresses")

        event = Event(
            timestamp=timestamp,
            source_ip=src_ip,
            destination_ip=dst_ip,
            source_port=src_port,
            destination_port=dst_port,
            protocol=protocol,
            payload=payload,
            raw=raw,
            collector=collector,
        )
        return NormalizationResult(event=event, discarded_fields={})

    def _extract_timestamp(self, payload: MutableMapping[str, Any]) -> datetime:
        for key in self.TIMESTAMP_KEYS:
            value = payload.pop(key, None)
            if value:
                if isinstance(value, datetime):
                    return value
                if isinstance(value, (int, float)):
                    return datetime.fromtimestamp(value)
                if isinstance(value, str):
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
        raise NormalizationError("Timestamp field not found")

    def _extract_ip(self, payload: MutableMapping[str, Any], keys: tuple[str, ...]) -> Optional[IPAddress]:
        for key in keys:
            value = payload.pop(key, None)
            if value:
                try:
                    return ip_address(value)
                except ValueError as exc:
                    raise NormalizationError(f"Invalid IP address: {value}") from exc
        return None

    def _extract_int(self, payload: MutableMapping[str, Any], keys: tuple[str, ...]) -> Optional[int]:
        for key in keys:
            value = payload.pop(key, None)
            if value is None:
                continue
            try:
                number = int(value)
            except (TypeError, ValueError) as exc:
                raise NormalizationError(f"Invalid number for {key}: {value}") from exc
            return number
        return None

    def _extract_str(self, payload: MutableMapping[str, Any], keys: tuple[str, ...]) -> Optional[str]:
        for key in keys:
            value = payload.pop(key, None)
            if isinstance(value, str):
                return value.lower()
            if value is not None:
                return str(value).lower()
        return None
