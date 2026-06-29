# NotifyMCP

NotifyMCP is a small FastMCP server that lets an agent publish messages to a configured MQTT topic.

It is intended to pair with the NotifyMQTT Android app: an agent calls the MCP tool, NotifyMCP publishes to MQTT, and NotifyMQTT turns that MQTT message into a phone notification.

## Tools

### `publish_message`

Publishes a message to the MQTT topic configured by environment variables.

Arguments:

- `message` — message payload to publish.
- `qos` — MQTT QoS level, defaults to `1`.
- `retain` — whether to publish as a retained MQTT message, defaults to `false`.

### `get_mqtt_config`

Returns the configured MQTT target without exposing the password.

## Environment variables

Required:

| Variable | Description |
| --- | --- |
| `MQTT_URL` | Broker URL. Supports `mqtt://`, `tcp://`, `mqtts://`, and `ssl://`. |
| `MQTT_TOPIC` | Topic to publish all agent messages to. |

Optional:

| Variable | Description |
| --- | --- |
| `MQTT_USERNAME` | MQTT username. Leave blank for anonymous brokers. |
| `MQTT_PASSWORD` | MQTT password. Leave blank for anonymous brokers. |
| `MQTT_KEEPALIVE_SECONDS` | MQTT keepalive. Defaults to `30`. |
| `MQTT_PUBLISH_TIMEOUT_SECONDS` | Publish wait timeout. Defaults to `10`. |

`mqtt://` and `tcp://` default to port `1883`. `mqtts://` and `ssl://` default to port `8883` and enable TLS.

## Run with uvx from GitHub

You can run the MCP server directly from the GitHub repo with uvx:

```bash
export MQTT_URL="mqtt://192.168.1.10:1883"
export MQTT_USERNAME=""
export MQTT_PASSWORD=""
export MQTT_TOPIC="notify/test"

uvx --from git+https://github.com/mbush91/NotifyMCP notifymcp
```

For a fixed version, use a tag or commit:

```bash
uvx --from git+https://github.com/mbush91/NotifyMCP@v0.1.0 notifymcp
```

## Example MCP client config

Use a command like this from an MCP-capable host that can launch `uvx`:

```json
{
  "mcpServers": {
    "notifymcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/mbush91/NotifyMCP",
        "notifymcp"
      ],
      "env": {
        "MQTT_URL": "mqtt://192.168.1.10:1883",
        "MQTT_USERNAME": "",
        "MQTT_PASSWORD": "",
        "MQTT_TOPIC": "notify/test"
      }
    }
  }
}
```

## Local development

```bash
uv sync --extra dev
uv run ruff check .
uv run pytest
uv build
```

You can also smoke-test the local checkout through uvx:

```bash
uvx --from . notifymcp
```
