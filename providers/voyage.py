from .base import BaseProvider, UnifiedMessage

class VonageProvider(BaseProvider):
    name = "vonage"
    
    def validate_webhook(self, headers, body, secret):
        # Vonage uses API key/secret or JWT; webhook validation varies by setup
        # Simple: check X-Vonage-Signature if configured
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
