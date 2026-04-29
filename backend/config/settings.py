"""Backend configuration settings."""
import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment."""

    model_config = ConfigDict(env_file=".env")

    # API Keys
    deepseek_api_key: str = ""
    openai_api_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "yaeteaching"

    # App
    app_name: str = "YaeTeaching API"
    debug: bool = False


settings = Settings()