"""Application configuration and settings management."""

from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR.parent / "config"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=CONFIG_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field("AnomalyDetector", env="APP_NAME")
    app_env: str = Field("development", env="APP_ENV")
    debug: bool = Field(True, env="APP_DEBUG")
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8080, env="API_PORT")
    cors_origins: str = Field("*", env="CORS_ORIGINS")

    db_host: str = Field("localhost", env="DB_HOST")
    db_port: int = Field(5432, env="DB_PORT")
    db_name: str = Field("anomaly", env="DB_NAME")
    db_user: str = Field("anomaly", env="DB_USER")
    db_password: str = Field("anomaly", env="DB_PASSWORD")

    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_db: int = Field(0, env="REDIS_DB")

    kafka_bootstrap: str = Field("localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    kafka_alert_topic: str = Field("anomaly-alerts", env="KAFKA_ALERT_TOPIC")
    kafka_events_topic: str = Field("anomaly-events", env="KAFKA_EVENTS_TOPIC")

    queue_backend: str = Field("redis", env="QUEUE_BACKEND")
    queue_stream_name: str = Field("anomaly-events", env="QUEUE_STREAM_NAME")
    queue_max_retries: int = Field(3, env="QUEUE_MAX_RETRIES")

    geoip_db_path: Optional[str] = Field(None, env="GEOIP_DB_PATH")
    asn_db_path: Optional[str] = Field(None, env="ASN_DB_PATH")

    slack_webhook_url: Optional[str] = Field(None, env="SLACK_WEBHOOK_URL")
    telegram_bot_token: Optional[str] = Field(None, env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(None, env="TELEGRAM_CHAT_ID")

    smtp_host: Optional[str] = Field(None, env="SMTP_HOST")
    smtp_port: Optional[int] = Field(None, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(None, env="SMTP_PASSWORD")
    smtp_from: Optional[str] = Field(None, env="SMTP_FROM")

    @field_validator("smtp_port", mode="before")
    @classmethod
    def _empty_str_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and value.strip() == "":
            return None
        return value

    jwt_secret: str = Field("change-me", env="JWT_SECRET")
    jwt_expires_in: int = Field(3600, env="JWT_EXPIRES_IN")


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()  # type: ignore[call-arg]


def settings_dict() -> dict[str, Any]:
    settings = get_settings()
    return settings.dict()
