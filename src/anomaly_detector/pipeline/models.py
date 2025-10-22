"""Core models used across pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from typing import Any, Mapping


IPAddress = IPv4Address | IPv6Address


@dataclass(slots=True)
class Event:
    """Normalized event structure emitted by collectors."""

    timestamp: datetime
    source_ip: IPAddress | None
    destination_ip: IPAddress | None
    source_port: int | None
    destination_port: int | None
    protocol: str | None
    payload: Mapping[str, Any] = field(default_factory=dict)
    raw: Any | None = None
    tags: set[str] = field(default_factory=set)
    collector: str | None = None

    def add_tag(self, tag: str) -> None:
        self.tags.add(tag)
