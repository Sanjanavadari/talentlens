from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "TalentLens API"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./talentlens.db"

    # Embedding model
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    # Output dimension of embedding_model_name (384 for all-MiniLM-L6-v2)
    embedding_dimension: int = 384

    # CORS — comma-separated origins; use * for local dev, set to your Vercel URL in production
    cors_origins: Annotated[str, Field(default="*")]

    # Upload limits
    max_upload_size_mb: int = 10
    max_resumes_per_request: int = 50

    # LLM explanations (optional — requires LLM_API_KEY)
    llm_api_key: str | None = None
    llm_model_name: str = "claude-sonnet-4-20250514"
    llm_provider: str | None = None  # "anthropic" | "openai"; auto-detected from model if unset
    llm_timeout_seconds: float = 15.0

    # JWT auth
    jwt_secret_key: str = "change-me-in-production-use-env-var"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    @field_validator("cors_origins", mode="before")
    @classmethod
    def normalize_cors_origins(cls, value: object) -> str:
        if value is None:
            return "*"
        if isinstance(value, list):
            return ",".join(str(item).strip() for item in value if str(item).strip())
        return str(value).strip() or "*"

    @property
    def cors_origin_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if raw == "*":
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    @property
    def cors_allow_credentials(self) -> bool:
        return "*" not in self.cors_origin_list

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def backend_root(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent


@lru_cache
def get_settings() -> Settings:
    return Settings()
