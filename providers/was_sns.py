import json
import hashlib
import hmac
import base64
from .base import BaseProvider, UnifiedMessage

class AWSSNSProvider(BaseProvider):
    name = "aws_sns"
    
    def validate_webhook(self, headers, body, secret):
        # AWS SNS uses certificate-based validation (recommended) or basic auth
        # For simplicity, you can verify the SNS signature using the SigningCertURL
        # Full implementation requires fetching the cert and verifying RSA signature
        return True  # TODO: implement cert validation
    
    def parse_payload(self, payload):
        # SNS sends JSON with Message field containing the SMS body
        message = json.loads(payload.get("Message", "{}"))
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
