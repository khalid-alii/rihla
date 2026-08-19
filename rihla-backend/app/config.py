from typing import Any, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    JWT_SECRET: str = "change-me-in-production"
    JWT_EXPIRY_DAYS: int = 30
    CORS_ORIGINS: str = "http://127.0.0.1:5500"

    SMTP_HOST: str = ""
    SMTP_PORT: Optional[int] = None
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@rihla.app"

    @field_validator("SMTP_PORT", mode="before")
    @classmethod
    def coerce_smtp_port(cls, v: Any) -> Optional[int]:
        """Allow SMTP_PORT= (blank) in .env without crashing."""
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return None
        return int(v)

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
