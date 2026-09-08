import hmac
import hashlib
import logging
from .base import BaseProvider, UnifiedMessage

logger = logging.getLogger("nexussms")


class VonageProvider(BaseProvider):
    name = "vonage"

    def validate_webhook(self, headers, body, secret):
        if not secret:
            return True
        sig = headers.get("X-Vonage-Signature", headers.get("x-vonage-signature", ""))
        if not sig:
            return False
        if isinstance(body, bytes):
            expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
            return hmac.compare_digest(sig, expected)
        return True

    def parse_payload(self, payload):
        return UnifiedMessage(
            provider="vonage",
            provider_message_id=payload.get("messageId", ""),
            sender=payload.get("msisdn", ""),
            recipient=payload.get("to", ""),
            body=payload.get("text", ""),
            timestamp=None,
            raw_payload=payload
        )

    def get_message_id(self, payload):
        return payload.get("messageId", "")
