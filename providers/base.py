from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class UnifiedMessage:
    provider: str
    provider_message_id: str
    sender: str
    recipient: str
    body: str
    timestamp: Optional[str]
    raw_payload: Dict[str, Any]


class BaseProvider(ABC):
    name: str = "base"

    @abstractmethod
    def validate_webhook(self, headers: Dict[str, str], body: bytes, secret: str) -> bool:
        pass

    @abstractmethod
    def parse_payload(self, payload: Dict[str, Any]) -> UnifiedMessage:
        pass

    @abstractmethod
    def get_message_id(self, payload: Dict[str, Any]) -> str:
        pass
