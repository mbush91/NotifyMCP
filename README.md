# NotifyMCP

NotifyMCP is a small containerized FastMCP server that lets an agent publish messages to a configured MQTT topic.

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

## Run locally

```bash
cp .env.example .env
# edit .env

docker compose build
docker compose run --rm notifymcp
```

The container runs the MCP server over stdio, which is the simplest mode for MCP hosts that launch tools as subprocesses/containers.

## Example MCP client config

Use a command like this from an MCP-capable host that can launch Docker:

```json
{
  "mcpServers": {
    "notifymcp": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env-file",
        "/absolute/path/to/NotifyMCP/.env",
        "notifymcp:local"
      ]
    }
  }
}
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
ruff check .
pytest
```
