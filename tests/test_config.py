from notifymcp.config import load_settings


def test_load_settings_defaults(monkeypatch):
    monkeypatch.setenv("MQTT_URL", "mqtt://broker.local")
    monkeypatch.setenv("MQTT_TOPIC", "notify/test")
    monkeypatch.delenv("MQTT_USERNAME", raising=False)
    monkeypatch.delenv("MQTT_PASSWORD", raising=False)

    settings = load_settings()

    assert settings.host == "broker.local"
    assert settings.port == 1883
    assert settings.use_tls is False
    assert settings.topic == "notify/test"
    assert settings.username is None
    assert settings.password is None


def test_load_settings_tls(monkeypatch):
    monkeypatch.setenv("MQTT_URL", "mqtts://broker.example.com")
    monkeypatch.setenv("MQTT_TOPIC", "notify/test")
    monkeypatch.setenv("MQTT_USERNAME", "user")
    monkeypatch.setenv("MQTT_PASSWORD", "secret")

    settings = load_settings()

    assert settings.host == "broker.example.com"
    assert settings.port == 8883
    assert settings.use_tls is True
    assert settings.username == "user"
    assert settings.password == "secret"
