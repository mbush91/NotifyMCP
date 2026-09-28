"""Simple HTTP POST endpoint for sending notifications via MQTT.

Uses only the standard library so no extra dependencies are required.

Endpoint:
    POST /notify  (alias: POST /publish)
    Headers: X-API-Key: <raw api key>
             (or: Authorization: Bearer <raw api key>)
    Body (JSON): {"message": "...", "qos": 1, "retain": false}

    GET /healthz -> {"ok": true} (no auth required)
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlsplit

from .auth import verify_api_key
from .config import MqttSettings, load_http_settings, load_settings

MAX_BODY_BYTES = 1024 * 1024
NOTIFY_PATHS = {"/notify", "/publish"}
HEALTH_PATHS = {"/healthz", "/health"}

PublishFn = Callable[..., dict[str, Any]]


def _extract_api_key(handler: BaseHTTPRequestHandler) -> str | None:
    key = handler.headers.get("X-API-Key")
    if key:
        return key.strip() or None
    auth = handler.headers.get("Authorization")
    if auth and auth.strip().lower().startswith("bearer "):
        token = auth.strip()[7:].strip()
        return token or None
    return None


class NotifyHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        mqtt_settings: MqttSettings,
        api_key_hash: str,
        publish_fn: PublishFn | None = None,
    ) -> None:
        from .publisher import publish_to_mqtt  # deferred to keep import light for tests

        super().__init__(address, NotifyHandler)
        self.mqtt_settings = mqtt_settings
        self.api_key_hash = api_key_hash
        self.publish_fn: PublishFn = publish_fn or publish_to_mqtt


class NotifyHandler(BaseHTTPRequestHandler):
    server: NotifyHTTPServer  # type: ignore[assignment]

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
        super().log_message(format, *args)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _path(self) -> str:
        return urlsplit(self.path).path.rstrip("/") or "/"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler name
        if self._path() in HEALTH_PATHS:
            self._send_json(200, {"ok": True})
            return
        self._send_json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler name
        if self._path() not in NOTIFY_PATHS:
            self._send_json(404, {"ok": False, "error": "not found"})
            return

        if not verify_api_key(_extract_api_key(self), self.server.api_key_hash):
            self._send_json(401, {"ok": False, "error": "invalid or missing API key"})
            return

        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            self._send_json(400, {"ok": False, "error": "invalid Content-Length"})
            return
        if length <= 0 or length > MAX_BODY_BYTES:
            self._send_json(400, {"ok": False, "error": "invalid Content-Length"})
            return

        try:
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"ok": False, "error": "body must be valid JSON"})
            return

        if not isinstance(data, dict):
            self._send_json(400, {"ok": False, "error": "body must be a JSON object"})
            return

        message = data.get("message", data.get("text", data.get("payload")))
        qos = data.get("qos", 1)
        retain = data.get("retain", False)

        if not isinstance(message, str) or not message:
            self._send_json(400, {"ok": False, "error": "message must be a non-empty string"})
            return
        # NOTE: bool is a subclass of int (True == 1), so check it explicitly
        # to keep the "qos must be numeric 0/1/2" contract.
        if isinstance(qos, bool) or qos not in (0, 1, 2):
            self._send_json(400, {"ok": False, "error": "qos must be 0, 1, or 2"})
            return
        if not isinstance(retain, bool):
            self._send_json(400, {"ok": False, "error": "retain must be a boolean"})
            return

        try:
            result = self.server.publish_fn(
                self.server.mqtt_settings, message, qos=qos, retain=retain
            )
        except ValueError as exc:
            self._send_json(400, {"ok": False, "error": str(exc)})
            return
        except Exception as exc:  # MQTT failures -> 502 so callers can distinguish upstream errors
            self._send_json(502, {"ok": False, "error": f"publish failed: {exc}"})
            return

        self._send_json(200, result)


def create_server(
    mqtt_settings: MqttSettings,
    host: str,
    port: int,
    api_key_hash: str,
    publish_fn: PublishFn | None = None,
) -> NotifyHTTPServer:
    return NotifyHTTPServer((host, port), mqtt_settings, api_key_hash, publish_fn)


def start_in_background(
    mqtt_settings: MqttSettings,
    host: str,
    port: int,
    api_key_hash: str,
    publish_fn: PublishFn | None = None,
) -> tuple[NotifyHTTPServer, threading.Thread]:
    server = create_server(mqtt_settings, host, port, api_key_hash, publish_fn)
    thread = threading.Thread(target=server.serve_forever, name="notify-http", daemon=True)
    thread.start()
    return server, thread


def main() -> None:
    mqtt_settings = load_settings()
    http_settings = load_http_settings()
    server = create_server(
        mqtt_settings, http_settings.host, http_settings.port, http_settings.api_key_hash
    )
    print(
        f"NotifyMCP HTTP listening on {http_settings.host}:{server.server_port} "
        f"(POST /notify, GET /healthz)"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
