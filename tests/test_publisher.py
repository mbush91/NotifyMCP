from notifymcp.config import MqttSettings
from notifymcp.publisher import publish_to_mqtt


class FakePublishInfo:
    rc = 0
    mid = 42

    def wait_for_publish(self, timeout=None):
        self.timeout = timeout


class FakeClient:
    def __init__(self):
        self.calls = []

    def username_pw_set(self, username, password=None):
        self.calls.append(("username_pw_set", username, password))

    def tls_set(self, *args, **kwargs):
        self.calls.append(("tls_set",))

    def connect(self, host, port, keepalive=60):
        self.calls.append(("connect", host, port, keepalive))
        return 0

    def loop_start(self):
        self.calls.append(("loop_start",))

    def publish(self, topic, payload, qos=0, retain=False):
        self.calls.append(("publish", topic, payload, qos, retain))
        return FakePublishInfo()

    def disconnect(self):
        self.calls.append(("disconnect",))

    def loop_stop(self):
        self.calls.append(("loop_stop",))


def test_publish_to_mqtt():
    fake = FakeClient()
    settings = MqttSettings(
        url="mqtt://broker.local:1883",
        username="user",
        password="secret",
        topic="notify/test",
        host="broker.local",
        port=1883,
        use_tls=False,
        keepalive_seconds=30,
        publish_timeout_seconds=10.0,
    )

    result = publish_to_mqtt(settings, "hello", qos=1, retain=False, client_factory=lambda: fake)

    assert result["ok"] is True
    assert result["topic"] == "notify/test"
    assert ("username_pw_set", "user", "secret") in fake.calls
    assert ("connect", "broker.local", 1883, 30) in fake.calls
    assert ("publish", "notify/test", "hello", 1, False) in fake.calls
