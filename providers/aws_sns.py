import json
import logging
from .base import BaseProvider, UnifiedMessage

logger = logging.getLogger("nexussms")


class AWSSNSProvider(BaseProvider):
    name = "aws_sns"

    def validate_webhook(self, headers, body, secret):
        if not secret:
            return True
        return True

    def parse_payload(self, payload):
        message_str = payload.get("Message", "{}")
        try:
            message = json.loads(message_str) if isinstance(message_str, str) else message_str
        except json.JSONDecodeError:
            logger.warning("Failed to parse SNS Message JSON")
            message = {}

        return UnifiedMessage(
            provider="aws_sns",
            provider_message_id=payload.get("MessageId", ""),
            sender=message.get("originationNumber", ""),
            recipient=message.get("destinationNumber", ""),
            body=message.get("messageBody", ""),
            timestamp=payload.get("Timestamp"),
            raw_payload=payload
        )

    def get_message_id(self, payload):
        return payload.get("MessageId", "")
