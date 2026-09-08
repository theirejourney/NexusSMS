# NexusSMS

Asynchronous-ready Python utility for capturing, parsing, and logging
incoming institutional SMS and OTP verification codes, delivered via Twilio
webhooks.

## Features

- **Pluggable extraction engine** — register custom institution rules at runtime
- **Twilio signature validation** — rejects forged webhooks
- **Idempotent ingestion** — Twilio `MessageSid` dedupe prevents double-logging
- **SQLite with WAL mode** — indexed, transaction-safe, zero-config
- **Callback hooks** — plug in Discord/Telegram/email notifications easily
- **Query API** — `GET /messages?sender=Chase&category=banking&limit=20`

## Quick start
pip install -r requirements.txtexport TWILIO_AUTH_TOKEN=your_tokenpython core/server.py
Point your Twilio Messaging webhook at `https://<your-host>/webhook/sms`.
from core.extractor import register_rule, parse_messageregister_rule("crypto", senders=["Coinbase", "Binance"],              
regex=r"code[^0-9]{0,10}([0-9]{4,8})")result = parse_message("Coinbase", "Your Coinbase code 90210")

Notifications via callbacks
from core.listener import MessageHandlerdef to_discord(result, inserted):    if inserted and result.extracted_code:        ...  # POST to your webhookhandler = MessageHandler(callbacks=[to_discord])
python -m unittest discover tests -v
