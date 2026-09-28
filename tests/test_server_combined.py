"""Regression tests for combined MCP (stdio) + HTTP mode.

Stdout is the MCP protocol stream when running over stdio, so starting the
HTTP sidecar must not write anything to stdout.
"""

import notifymcp.server as server_module
from notifymcp.auth import hash_api_key


def test_combined_mode_banner_goes_to_stderr_not_stdout(monkeypatch, capsys):
    monkeypatch.setenv("MQTT_URL", "mqtt://broker.local")
    monkeypatch.setenv("MQTT_TOPIC", "notify/test")
    monkeypatch.setenv("HTTP_ENABLED", "true")
    monkeypatch.setenv("NOTIFY_API_KEY_HASH", hash_api_key("test-key"))

    started = {}

    class FakeServer:
        server_port = 8080

    def fake_start(mqtt_settings, host, port, api_key_hash, publish_fn=None):
        started.update(
            {"host": host, "port": port, "topic": mqtt_settings.topic, "hash": api_key_hash}
        )
        return FakeServer(), object()

    ran = {}
    # NOTE: main() imports start_in_background locally, so patch it at its source.
    monkeypatch.setattr("notifymcp.http_server.start_in_background", fake_start)
    monkeypatch.setattr(server_module.mcp, "run", lambda: ran.update({"called": True}))

    server_module.main()

    assert ran.get("called") is True
    assert started["topic"] == "notify/test"
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "POST /notify" in captured.err


def test_mcp_only_mode_does_not_start_http(monkeypatch, capsys):
    monkeypatch.setenv("HTTP_ENABLED", "")
    monkeypatch.delenv("NOTIFY_API_KEY_HASH", raising=False)

    def fail_start(*args, **kwargs):
        raise AssertionError("HTTP server must not start when HTTP_ENABLED is not set")

    ran = {}
    monkeypatch.setattr("notifymcp.http_server.start_in_background", fail_start)
    monkeypatch.setattr(server_module.mcp, "run", lambda: ran.update({"called": True}))

    server_module.main()

    assert ran.get("called") is True
    assert capsys.readouterr().out == ""
