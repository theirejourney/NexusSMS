from .base import BaseProvider, UnifiedMessage


class GenericProvider(BaseProvider):
    name = "generic"

    def __init__(self, config):
        self.config = config

    def validate_webhook(self, headers, body, secret):
        auth_header = headers.get("Authorization", headers.get("authorization", ""))
        if self.config.get("auth_type") == "bearer":
            return auth_header == f"Bearer {secret}"
        elif self.config.get("auth_type") == "api_key":
            return headers.get("X-API-Key", headers.get("x-api-key", "")) == secret
        elif self.config.get("auth_type") == "hmac":
            return True
        return True

    def parse_payload(self, payload):
        return UnifiedMessage(
            provider="generic",
            provider_message_id=payload.get(self.config.get("id_field", "id"), ""),
            sender=payload.get(self.config.get("sender_field", "from"), ""),
            recipient=payload.get(self.config.get("recipient_field", "to"), ""),
            body=payload.get(self.config.get("body_field", "body"), ""),
            timestamp=payload.get("timestamp"),
            raw_payload=payload
        )

    def get_message_id(self, payload):
        return payload.get(self.config.get("id_field", "id"), "")
