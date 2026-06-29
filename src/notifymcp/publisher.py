from __future__ import annotations

from dataclasses import asdict
from typing import Any, Protocol

import paho.mqtt.client as mqtt

from .config import MqttSettings


class MqttPublishError(RuntimeError):
    pass


class _PublishInfo(Protocol):
    rc: int
    mid: int

    def wait_for_publish(self, timeout: float | None = None) -> None: ...


class _Client(Protocol):
    def username_pw_set(self, username: str, password: str | None = None) -> None: ...
    def tls_set(self, *args: Any, **kwargs: Any) -> None: ...
    def connect(self, host: str, port: int, keepalive: int = 60) -> int: ...
    def loop_start(self) -> None: ...
    def publish(
        self, topic: str, payload: str, qos: int = 0, retain: bool = False
    ) -> _PublishInfo: ...
    def disconnect(self) -> None: ...
    def loop_stop(self) -> None: ...


def _new_client() -> _Client:
    return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)


def publish_to_mqtt(
    settings: MqttSettings,
    payload: str,
    *,
    qos: int = 1,
    retain: bool = False,
    client_factory: Any = _new_client,
) -> dict[str, Any]:
    if qos not in {0, 1, 2}:
        raise ValueError("qos must be 0, 1, or 2")
    if payload == "":
        raise ValueError("payload must not be empty")

    client = client_factory()
    loop_started = False

    try:
        if settings.username is not None:
            client.username_pw_set(settings.username, settings.password)
        if settings.use_tls:
            client.tls_set()

        connect_rc = client.connect(
            settings.host, settings.port, keepalive=settings.keepalive_seconds
        )
        if connect_rc != mqtt.MQTT_ERR_SUCCESS:
            raise MqttPublishError(f"MQTT connect failed with rc={connect_rc}")

        client.loop_start()
        loop_started = True

        info = client.publish(settings.topic, payload, qos=qos, retain=retain)
        info.wait_for_publish(timeout=settings.publish_timeout_seconds)

        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise MqttPublishError(f"MQTT publish failed with rc={info.rc}")

        return {
            "ok": True,
            "topic": settings.topic,
            "qos": qos,
            "retain": retain,
            "mid": info.mid,
            "broker": {
                key: value
                for key, value in asdict(settings).items()
                if key not in {"username", "password"}
            },
        }
    finally:
        try:
            client.disconnect()
        finally:
            if loop_started:
                client.loop_stop()
