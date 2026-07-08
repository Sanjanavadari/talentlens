from functools import lru_cache
from pathlib import Path

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

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

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

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def backend_root(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent


@lru_cache
def get_settings() -> Settings:
    return Settings()
