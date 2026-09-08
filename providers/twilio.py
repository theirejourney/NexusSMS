from twilio.request_validator import RequestValidator
from .base import BaseProvider, UnifiedMessage


class TwilioProvider(BaseProvider):
    name = "twilio"
    
    def validate_webhook(self, headers, body, secret):
        validator = RequestValidator(secret)
        proto = headers.get("x-forwarded-proto", "https")
        host = headers.get("host", "localhost")
        url = headers.get("x-twilio-webhook-url") or f"{proto}://{host}/webhook/twilio"
        signature = headers.get("x-twilio-signature", "")
        
        if isinstance(body, dict):
            return validator.validate(url, body, signature)
        return False
    
    def parse_payload(self, payload):
        return UnifiedMessage(
            provider="twilio",
            provider_message_id=payload.get("MessageSid", ""),
            sender=payload.get("From", ""),
            recipient=payload.get("To", ""),
            body=payload.get("Body", ""),
            timestamp=None,
            raw_payload=payload
        )
    
    def get_message_id(self, payload):
        return payload.get("MessageSid", "")
