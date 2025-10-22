"""Slack alert channel implementation."""

from __future__ import annotations

import json
from typing import Any

from anomaly_detector.alerts.base import Alert, AlertChannel
from anomaly_detector.config import get_settings


class SlackWebhookChannel(AlertChannel):
    """Deliver alerts to Slack via incoming webhook."""

    def __init__(self, *, webhook_url: str | None = None) -> None:
        super().__init__(name="slack")
        settings = get_settings()
        self._webhook_url = webhook_url or settings.slack_webhook_url

    async def send(self, alert: Alert) -> None:
        if not self._webhook_url:
            return

        payload: dict[str, Any] = {
            "text": f"[{alert.severity.upper()}] {alert.title}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*{alert.title}*\n"
                            f"Severity: `{alert.severity}`\n"
                            f"Source: `{alert.event.source_ip}` → `{alert.event.destination_ip}`\n"
                            f"Protocol: `{alert.event.protocol}`\n"
                        ),
                    },
                }
            ],
        }

        # Lazy import to avoid hard dependency at startup when Slack not configured.
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(self._webhook_url, content=json.dumps(payload))
            response.raise_for_status()
