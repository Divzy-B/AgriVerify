from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AgriVerify"
    api_prefix: str = "/api/v1"
    agriverify_demo_mode: bool = True
    database_url: str = "sqlite:///./agriverify.db"
    api_key: str = ""
    allowed_origins: str = "http://localhost:3000"
    voice_provider: str = "bolna"
    bolna_api_key: str = ""
    bolna_agent_id: str = ""
    bolna_webhook_secret: str = ""
    earth_engine_project: str = ""
    earth_engine_service_account: str = ""
    earth_engine_private_key_json: str = ""
    verification_tolerance_days: int = 7
    max_planting_age_days: int = 548  # about 18 months; older planting dates are rejected outside demo mode

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [value.strip() for value in self.allowed_origins.split(",") if value.strip()]

    @property
    def earth_engine_configured(self) -> bool:
        # Service-account key is optional: without one, Earth Engine uses application-default credentials.
        return bool(self.earth_engine_project)

    @property
    def bolna_configured(self) -> bool:
        return bool(self.bolna_api_key and self.bolna_agent_id)


@lru_cache
def get_settings() -> Settings:
    return Settings()

