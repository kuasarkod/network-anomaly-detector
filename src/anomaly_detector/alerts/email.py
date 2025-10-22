"""Email alert channel implementation."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from anomaly_detector.alerts.base import Alert, AlertChannel
from anomaly_detector.config import get_settings


class SMTPEmailChannel(AlertChannel):
    """Send alerts via SMTP email."""

    def __init__(self, *, smtp_host: str | None = None, smtp_port: int | None = None) -> None:
        super().__init__(name="email")
        settings = get_settings()
        self._host = smtp_host or settings.smtp_host
        self._port = smtp_port or settings.smtp_port
        self._username = settings.smtp_username
        self._password = settings.smtp_password
        self._sender = settings.smtp_from

    async def send(self, alert: Alert) -> None:
        if not self._host or not self._sender:
            return

        msg = EmailMessage()
        msg["Subject"] = f"[{alert.severity.upper()}] {alert.title}"
        msg["From"] = self._sender
        msg["To"] = self._sender
        msg.set_content(
            (
                f"Alert: {alert.title}\n"
                f"Severity: {alert.severity}\n"
                f"Source: {alert.event.source_ip} -> {alert.event.destination_ip}\n"
                f"Protocol: {alert.event.protocol}\n"
            )
        )

        loop = __import__("asyncio").get_event_loop()
        await loop.run_in_executor(None, self._send_email_sync, msg)

    def _send_email_sync(self, message: EmailMessage) -> None:
        if self._username and self._password:
            with smtplib.SMTP(self._host, self._port or 587) as server:
                server.starttls()
                server.login(self._username, self._password)
                server.send_message(message)
        else:
            with smtplib.SMTP(self._host, self._port or 25) as server:
                server.send_message(message)
