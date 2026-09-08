from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class UnifiedMessage:
    provider: str           # "twilio", "aws_sns", "vonage", etc.
    provider_message_id: str  # Original ID from provider
    sender: str             # E.164 phone number or alphanumeric
    recipient: str          # E.164 phone number
    body: str               # Message content
    timestamp: Optional[str]  # ISO 8601
    raw_payload: Dict[str, Any]

class BaseProvider(ABC):
    name: str = "base"
    
    @abstractmethod
    def validate_webhook(self, headers: Dict[str, str], body: bytes, secret: str) -> bool:
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
