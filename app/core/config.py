import os
import secrets
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_database_url() -> str:
    if os.getenv("VERCEL"):
        return "sqlite:////tmp/reembolsabr.db"
    return "sqlite:///./reembolso.db"


class Settings(BaseSettings):
    app_name: str = "ReembolsaBR API"
    api_prefix: str = "/api/v1"
    database_url: str = default_database_url()
    redis_url: str = "redis://localhost:6379/0"
    # A random development key is safer than a well-known fallback. Deployments must
    # still provide a persistent SECRET_KEY so tokens survive process restarts.
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(48), repr=False)
    access_token_expire_minutes: int = Field(default=60, ge=1, le=1440)
    jwt_issuer: str = "reembolsabr"
    jwt_audience: str = "reembolsabr-api"
    seed_admin_email: str | None = None
    seed_admin_password: str | None = None
    seed_admin_full_name: str = "Administrador"
    seed_admin_organization: str = "ReembolsaBR"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", validate_default=True)

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        known_defaults = {
            "development-secret-change-in-production",
            "change-this-at-least-32-characters",
        }
        if len(value) < 32 or value.lower() in known_defaults:
            raise ValueError("SECRET_KEY deve ser aleatória e ter pelo menos 32 caracteres")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
