from __future__ import annotations

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Aircraft Design ChatUI"
    app_version: str = "1.0.0"
    debug: bool = False

    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    websocket_heartbeat_interval: int = 30
    websocket_reconnection_attempts: int = 5

    skill_timeout: int = 300
    skill_max_concurrent_tasks: int = 5

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    static_files_dir: str = "static"
    models_dir: str = "static/models"
    envelopes_dir: str = "static/envelopes"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
