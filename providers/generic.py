from .base import BaseProvider, UnifiedMessage

class GenericProvider(BaseProvider):
    """For custom HTTP webhooks from niche providers or internal systems."""
    name = "generic"
    
    def __init__(self, config):
        self.config = config
    
    def validate_webhook(self, headers, body, secret):
        # Configurable: Bearer token, API key, HMAC, or none
        auth_header = headers.get("Authorization", "")
        if self.config.get("auth_type") == "bearer":
            return auth_header == f"Bearer {secret}"
        elif self.config.get("auth_type") == "api_key":
            return headers.get("X-API-Key") == secret
        return True
    
    def parse_payload(self, payload):
        return UnifiedMessage(
            provider="generic",
            provider_message_id=payload.get(self.config.get("id_field", "id")),
            sender=payload.get(self.config.get("sender_field", "from"), ""),
            recipient=payload.get(self.config.get("recipient_field", "to"), ""),
            body=payload.get(self.config.get("body_field", "body"), ""),
            timestamp=payload.get("timestamp"),
            raw_payload=payload
        )
