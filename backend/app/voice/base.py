from abc import ABC, abstractmethod
from typing import Any


class VoiceProvider(ABC):
    """Vendor boundary. Business services consume normalized data only."""

    @abstractmethod
    async def initiate_call(self, *, recipient_phone_number: str, language: str, user_data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def normalize_event(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    async def retrieve_call(self, provider_session_id: str) -> dict[str, Any]: ...

