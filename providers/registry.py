from typing import Dict, Type
from .base import BaseProvider
from .twilio import TwilioProvider
from .aws_sns import AWSSNSProvider
from .vonage import VonageProvider
from .generic import GenericProvider

_PROVIDER_MAP: Dict[str, Type[BaseProvider]] = {
    "twilio": TwilioProvider,
    "aws_sns": AWSSNSProvider,
    "vonage": VonageProvider,
    "generic": GenericProvider,
}

class ProviderRegistry:
    def __init__(self, config: dict):
        self._providers: Dict[str, BaseProvider] = {}
        for name, provider_class in _PROVIDER_MAP.items():
            if name in config:
                self._providers[name] = provider_class(config[name])
    
    def get(self, name: str) -> BaseProvider:
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not configured")
        return self._providers[name]
    
    def list_active(self):
        return list(self._providers.keys())
