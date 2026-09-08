import json
import base64
from urllib.parse import urlsplit

import httpx
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from .base import BaseProvider, UnifiedMessage


class AWSSNSProvider(BaseProvider):
    name = "aws_sns"
    
    def __init__(self, config):
        self.config = config
        self._cert_cache: dict[str, str] = {}
    
    def validate_webhook(self, headers, body, secret):
        if isinstance(body, bytes):
            try:
                payload
