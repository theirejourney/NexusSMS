from twilio.request_validator import RequestValidator
from .base import BaseProvider, UnifiedMessage

class TwilioProvider(BaseProvider):
    name = "twilio"
    
    def validate_webhook(self, headers, body, secret):
        validator = RequestValidator(secret)
        url = headers.get("X-Forwarded-Proto", "https") + "://" + headers.get("Host", "") + "/webhook/twilio"
        signature = headers.get("X-Twilio-Signature", "")
        return validator.validate(url, payload=dict(body), signature=signature)
    
    def parse_payload(self, payload):
        return UnifiedMessage(
            provider="twilio",
            provider_message_id=payload["MessageSid"],
            sender=payload.get("From", ""),
            recipient=payload.get("To", ""),
            body=payload.get("Body", ""),
            timestamp=None,
            raw_payload=payload
        )
    
    def get_message_id(self, payload):
        return payload["MessageSid"]
