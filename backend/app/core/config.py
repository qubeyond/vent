from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres
    database_url: str = "postgresql+asyncpg://braindump:braindump@localhost:5432/braindump"

    # Auth
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 14  # 14 days — personal single-user app

    @field_validator("secret_key")
    @classmethod
    def _secret_key_must_be_set(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError(
                "SECRET_KEY must be set and at least 32 characters — "
                "generate one with: openssl rand -hex 32"
            )
        return value

    # RouterAI (https://routerai.ru/docs/guides) — OpenAI-compatible LLM router
    routerai_api_key: str
    routerai_base_url: str = "https://routerai.ru/api/v1"
    llm_model: str = "openai/gpt-4o-mini"
    llm_timeout_seconds: float = 30.0

    # CORS — comma-separated list of allowed origins for dev (prod is same-origin via Caddy)
    cors_origins: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
