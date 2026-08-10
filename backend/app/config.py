"""
Central application configuration.
Loaded from environment variables (see .env.example).
Never hardcode secrets here - this file only defines defaults for local dev.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://media_user:change_me@localhost:5432/media_pipeline"

    # Redis / Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Auth
    jwt_secret_key: str = "dev-only-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Uploads
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10
    allowed_mime_types: str = "image/jpeg,image/png,image/webp"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Rate limiting
    login_rate_limit: str = "5/minute"
    register_rate_limit: str = "5/minute"
    upload_rate_limit: str = "20/minute"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def allowed_mime_list(self) -> list[str]:
        return [m.strip() for m in self.allowed_mime_types.split(",")]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
