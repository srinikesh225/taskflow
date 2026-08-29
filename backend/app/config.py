"""Application configuration, loaded from environment / .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- core ---
    app_name: str = "TaskFlow"
    environment: str = "development"  # development | production

    # --- security ---
    # MUST be overridden in production via the SECRET_KEY env var.
    secret_key: str = "dev-only-insecure-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- database ---
    database_url: str = "sqlite:///./taskflow.db"

    # --- CORS ---
    # Comma-separated list of allowed origins for the browser frontend.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- logging ---
    log_level: str = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
