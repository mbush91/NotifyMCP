import json
import threading
import urllib.error
import urllib.request

from notifymcp.auth import hash_api_key
from notifymcp.config import MqttSettings
from notifymcp.http_server import create_server

API_KEY = "test-key-123"


def _settings():
    return MqttSettings(
        url="mqtt://broker.local:1883",
        username=None,
        password=None,
        topic="notify/test",
        host="broker.local",
        port=1883,
        use_tls=False,
        keepalive_seconds=30,
        publish_timeout_seconds=10.0,
    )


def _serve(publish_fn):
    server = create_server(_settings(), "127.0.0.1", 0, hash_api_key(API_KEY), publish_fn)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _post(server, path, body, api_key=API_KEY, headers=None):
    url = f"http://127.0.0.1:{server.server_port}{path}"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        method="POST",
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    if api_key is not None:
        req.add_header("X-API-Key", api_key)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode())


def test_http_notify_success_and_auth():
    calls = []

    def fake_publish(settings, message, *, qos=1, retain=False):
        calls.append((message, qos, retain))
        return {"ok": True, "topic": settings.topic, "qos": qos, "retain": retain}

    server = _serve(fake_publish)
    try:
        status, body = _post(server, "/notify", {"message": "hello"})
        assert status == 200
        assert body["ok"] is True
        assert calls == [("hello", 1, False)]

        status, body = _post(server, "/notify", {"message": "hi", "qos": 0, "retain": True})
        assert status == 200
        assert calls[-1] == ("hi", 0, True)

        status, _ = _post(server, "/notify", {"message": "hello"}, api_key="wrong")
        assert status == 401

        status, _ = _post(server, "/notify", {"message": "hello"}, api_key=None)
        assert status == 401

        status, _ = _post(server, "/notify", {"qos": 1})
        assert status == 400

        status, _ = _post(server, "/notify", {"message": "hello", "qos": 5})
        assert status == 400

        # bool is a subclass of int (True == 1) but must not be accepted as qos
        status, body = _post(server, "/notify", {"message": "hello", "qos": True})
        assert status == 400
        assert body["error"] == "qos must be 0, 1, or 2"

        status, _ = _post(server, "/notify", {"message": "hello", "qos": False})
        assert status == 400
    finally:
        server.shutdown()
        server.server_close()


def test_http_health_no_auth():
    server = _serve(lambda *a, **k: {"ok": True})
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/healthz") as resp:
            assert resp.status == 200
            assert json.loads(resp.read().decode()) == {"ok": True}
    finally:
        server.shutdown()
        server.server_close()
