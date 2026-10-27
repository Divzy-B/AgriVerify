from typing import Any

import httpx

from app.core.config import Settings
from app.voice.base import VoiceProvider


class BolnaVoiceProvider(VoiceProvider):
    """Thin adapter for documented Bolna REST call and execution workflows."""
    api_base = "https://api.bolna.ai"

    def __init__(self, settings: Settings):
        self.settings = settings

    def _headers(self) -> dict[str, str]:
        if not self.settings.bolna_configured:
            raise RuntimeError("Bolna is not configured. Set BOLNA_API_KEY and BOLNA_AGENT_ID; use the text simulator locally.")
        return {"Authorization": f"Bearer {self.settings.bolna_api_key}", "Content-Type": "application/json"}

    async def initiate_call(self, *, recipient_phone_number: str, language: str, user_data: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "agent_id": self.settings.bolna_agent_id,
            "recipient_phone_number": recipient_phone_number,
            "agent_data": {"language": language},
            "user_data": user_data,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f"{self.api_base}/call", headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()

    async def retrieve_call(self, provider_session_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{self.api_base}/call/{provider_session_id}", headers=self._headers())
            response.raise_for_status()
            return response.json()

    def normalize_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        # Bolna sends execution payloads for configured agent webhooks. Keep only
        # fields usable by the vendor-neutral aggregate and preserve raw payload in audit logs.
        return {
            "provider_session_id": str(payload.get("execution_id") or payload.get("id") or payload.get("call_id") or ""),
            "status": str(payload.get("status") or "UNKNOWN").upper().replace("-", "_"),
            "transcript": payload.get("transcript") or payload.get("conversation") or [],
            "language": str((payload.get("agent_data") or {}).get("language") or "en"),
            "raw": payload,
        }

