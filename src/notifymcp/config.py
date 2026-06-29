from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class MqttSettings:
    url: str
    username: str | None
    password: str | None
    topic: str
    host: str
    port: int
    use_tls: bool
    keepalive_seconds: int
    publish_timeout_seconds: float


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a number") from exc


def load_settings() -> MqttSettings:
    url = _required_env("MQTT_URL")
    topic = _required_env("MQTT_TOPIC")
    parsed = urlparse(url)

    if parsed.scheme not in {"mqtt", "mqtts", "tcp", "ssl"}:
        raise RuntimeError("MQTT_URL must start with mqtt://, mqtts://, tcp://, or ssl://")
    if not parsed.hostname:
        raise RuntimeError("MQTT_URL must include a host")

    use_tls = parsed.scheme in {"mqtts", "ssl"}
    default_port = 8883 if use_tls else 1883

    return MqttSettings(
        url=url,
        username=_optional_env("MQTT_USERNAME"),
        password=_optional_env("MQTT_PASSWORD"),
        topic=topic,
        host=parsed.hostname,
        port=parsed.port or default_port,
        use_tls=use_tls,
        keepalive_seconds=_int_env("MQTT_KEEPALIVE_SECONDS", 30),
        publish_timeout_seconds=_float_env("MQTT_PUBLISH_TIMEOUT_SECONDS", 10.0),
    )
