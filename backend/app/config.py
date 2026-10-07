from pathlib import Path
from urllib.parse import unquote, urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_env: str = "development"
    serve_frontend: bool = False
    frontend_dist: Path = BACKEND_DIR.parent / "frontend" / "dist"

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "mysql_ai_assistant"
    mysql_password: str = ""
    mysql_database: str = "mysql_ai_lab"
    mysql_url: str = ""
    mysql_connect_timeout: int = 8
    mysql_ssl_disabled: bool = False
    mysql_ssl_ca: str | None = None
    mysql_ssl_verify_cert: bool = False
    mysql_ssl_verify_identity: bool = False

    ai_provider: str = "ollama"

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_api_key: str = ""
    ollama_model: str = "qwen2.5:3b"
    ollama_timeout: float = 120.0
    ollama_health_timeout: float = 3.0
    ollama_keep_alive: str = "10m"
    ollama_num_ctx: int = 4096
    ollama_num_gpu: int = -1
    ollama_temperature: float = 0.1

    openrouter_api_key: str = ""
    openrouter_model: str = "cohere/north-mini-code:free"
    openrouter_url: str = "https://openrouter.ai/api/v1/chat/completions"
    openrouter_timeout: float = 60.0

    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173"
    )
    max_result_rows: int = 1000
    pending_plan_expiry_minutes: int = 10

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def normalized_ai_provider(self) -> str:
        return self.ai_provider

    @property
    def effective_mysql_database(self) -> str:
        if not self.mysql_url:
            return self.mysql_database
        return unquote(urlparse(self.mysql_url).path.lstrip("/")) or self.mysql_database

    @field_validator("ai_provider")
    @classmethod
    def validate_ai_provider(cls, value: str) -> str:
        provider = value.strip().lower()
        if provider not in {"ollama", "openrouter"}:
            raise ValueError("AI_PROVIDER must be either 'ollama' or 'openrouter'.")
        return provider

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
