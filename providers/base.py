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
    def validate_webhook(self, headers: Dict[str, str], body, secret: str) -> bool:
        """Verify webhook authenticity using provider-specific signature."""
        pass
    
    @abstractmethod
    def parse_payload(self, payload: Dict[str, Any]) -> UnifiedMessage:
        """Convert provider-specific payload to unified format."""
        pass
    
    @abstractmethod
    def get_message_id(self, payload: Dict[str, Any]) -> str:
        """Extract unique message ID for deduplication."""
        pass
