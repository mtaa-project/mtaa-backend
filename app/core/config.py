import os

from pydantic_settings import BaseSettings, SettingsConfigDict

ENVIRONMENT = os.getenv("RENDER_ENV", "development")


class Settings(BaseSettings):
    app_name: str = "MTAA project 2025"
    db_user: str
    db_password: str
    db_name: str
    db_host: str
    testing: str | None = None
    model_config = SettingsConfigDict(
        env_file=".env" if ENVIRONMENT != "production" else None,
        env_file_encoding="utf-8",
    )


config = Settings()
