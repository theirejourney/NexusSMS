from twilio.request_validator import RequestValidator
from .base import BaseProvider, UnifiedMessage
from urllib.parse import parse_qs


class TwilioProvider(BaseProvider):
    name = "twilio"

    def validate_webhook(self, headers, body, secret):
        if not secret:
            return True
        validator = RequestValidator(secret)
        proto = headers.get("X-Forwarded-Proto", headers.get("x-forwarded-proto", "https"))
        host = headers.get("X-Forwarded-Host", headers.get("x-forwarded-host",
                         headers.get("Host", headers.get("host", "localhost"))))
        url = f"{proto}://{host}/webhook/twilio"
        signature = headers.get("X-Twilio-Signature", headers.get("x-twilio-signature", ""))

        if isinstance(body, bytes):
            parsed = parse_qs(body.decode("utf-8"))
            params = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
        else:
            params = dict(body) if body else {}

        return validator.validate(url, params, signature)

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
