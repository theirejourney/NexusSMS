"""Twilio webhook server — signature-validated, idempotent, production-ready.

Environment variables:
    TWILIO_AUTH_TOKEN   required for request signature validation
    NEXUSSMS_DB         SQLite path (default: nexus_sms.db)
    HOST                default 0.0.0.0
    PORT                default 5000
    FLASK_DEBUG         default 0 (never enable in production)
"""

from __future__ import annotations

import logging
import os

from flask import Flask, jsonify, request
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from core.database import get_recent_messages
from core.listener import MessageHandler

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("nexussms.server")

app = Flask(__name__)
handler = MessageHandler(db_path=os.environ.get("NEXUSSMS_DB", "nexus_sms.db"))

validator: RequestValidator | None = None
_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
if _auth_token:
    validator = RequestValidator(_auth_token)
else:
    logger.warning("TWILIO_AUTH_TOKEN not set — signature validation DISABLED. "
                   "Do not expose this server publicly without it.")


def _signature_valid() -> bool:
    if validator is None:
        return True  # local dev only
    sig = request.headers.get("X-Twilio-Signature", "")
    # Behind a proxy, Twilio signs the public URL — override if needed.
    public_url = os.environ.get("PUBLIC_BASE_URL", request.url)
    return validator.validate(public_url, request.form.to_dict(), sig)


@app.route("/webhook/sms", methods=["POST"])
def sms_webhook():
    if not _signature_valid():
        logger.warning("rejected request with invalid Twilio signature")
        return "Forbidden", 403

    message_sid = request.form.get("MessageSid", "")
    sender = request.form.get("From", "Unknown")
    body = request.form.get("Body", "")

    try:
        handler.handle(sender, body, message_sid=message_sid)
    except Exception:
        # Always 200 to Twilio after validation — its retries would only
        # duplicate work; logging captures the failure for you to inspect.
        logger.exception("failed to process sid=%s", message_sid)

    return str(MessagingResponse())


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok", processed=handler.processed,
                   duplicates=handler.duplicates)


@app.route("/messages", methods=["GET"])
def messages():
    limit = min(int(request.args.get("limit", 10)), 200)
    return jsonify(get_recent_messages(
        limit=limit,
        sender=request.args.get("sender"),
        category=request.args.get("category"),
        db_path=handler.db_path,
    ))


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "0.0.0.0"),
            port=int(os.environ.get("PORT", 5000)),
            debug=os.environ.get("FLASK_DEBUG", "0") == "1")
