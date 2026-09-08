# NexusSMS By IRE

Asynchronous-ready Python utility for capturing, parsing, and logging incoming institutional SMS and OTP verification codes via webhooks.

## Features

- **Pluggable extraction engine** — register custom institution rules at runtime
- **Multi-provider support** — Twilio, AWS SNS, Vonage, and generic webhooks
- **Webhook signature validation** — rejects forged requests per-provider
- **Idempotent ingestion** — provider message ID deduplication prevents double-logging
- **SQLite with WAL mode** — indexed, transaction-safe, zero-config
- **Callback hooks** — plug in Discord, Telegram, email notifications easily
- **Query API** — `GET /messages?sender=Chase&category=banking&limit=20`
- **Rate limiting** — 60 req/min per IP out of the box
- **Docker ready** — includes Dockerfile and docker-compose

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure secrets

```bash
cp .env.example .env
# Edit .env and add your Twilio Auth Token
```

### 3. Run the server

```bash
python main.py server --port 5000
```

Point your Twilio Messaging webhook at `https://<your-host>/webhook/twilio`.

## Registering Custom Rules

```python
from core.extractor import register_rule, parse_message

register_rule(
    "crypto",
    senders=["Coinbase", "Binance"],
    regex=r"(?:code|verify)[^0-9]{0,10}([0-9]{4,8})"
)

result = parse_message("Coinbase", "Your Coinbase code 90210")
print(result.extracted_code)  # 90210
```

## Notifications via Callbacks

```python
from core.listener import MessageHandler

def to_discord(result, inserted):
    if inserted and result.extracted_code:
        # POST to your Discord webhook
        pass

handler = MessageHandler(callbacks=[to_discord])
```

## Docker

```bash
docker-compose up --build
```

## Running Tests

```bash
pytest tests/ -v
# or
python -m unittest discover tests -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhook/{provider}` | Ingest webhook from configured provider |
| GET | `/messages` | Query stored messages |
| GET | `/health` | Health check |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TWILIO_AUTH_TOKEN` | — | Twilio auth token for webhook validation |
| `NEXUSSMS_DB` | `nexus_sms.db` | SQLite database path |
| `NEXUSSMS_CONFIG` | `config.json` | Provider configuration file |
| `PORT` | `5000` | Server port |
| `HOST` | `0.0.0.0` | Server bind host |

## License

MIT
