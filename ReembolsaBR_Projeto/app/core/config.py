from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ReembolsaBR API"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./reembolso.db"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "development-secret-change-in-production"
    access_token_expire_minutes: int = 60
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
