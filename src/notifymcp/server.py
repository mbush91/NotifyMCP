from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from .config import load_settings
from .publisher import publish_to_mqtt

mcp = FastMCP("NotifyMCP")


@mcp.tool
def publish_message(message: str, qos: int = 1, retain: bool = False) -> dict[str, Any]:
    """Publish a message to the configured MQTT topic.

    The broker URL, username, password, and topic are configured through the
    container environment: MQTT_URL, MQTT_USERNAME, MQTT_PASSWORD, MQTT_TOPIC.
    """
    settings = load_settings()
    return publish_to_mqtt(settings, message, qos=qos, retain=retain)


@mcp.tool
def get_mqtt_config() -> dict[str, Any]:
    """Return the configured MQTT target, excluding secrets."""
    settings = load_settings()
    return {
        "url": settings.url,
        "host": settings.host,
        "port": settings.port,
        "use_tls": settings.use_tls,
        "topic": settings.topic,
        "username_configured": settings.username is not None,
        "password_configured": settings.password is not None,
        "keepalive_seconds": settings.keepalive_seconds,
        "publish_timeout_seconds": settings.publish_timeout_seconds,
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
