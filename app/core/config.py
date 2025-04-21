import os
from enum import StrEnum

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"
    STAGING = "staging"


ENVIRONMENT = os.getenv("RENDER_ENV", Environment.DEVELOPMENT)


class Settings(BaseSettings):
    app_name: str = "MTAA - APP"
    db_user: str
    db_password: str
    db_name: str
    db_host: str
    db_port: int
    testing: str | None = None
    render_env: str = ENVIRONMENT

    model_config = SettingsConfigDict(
        env_file=".env" if ENVIRONMENT != Environment.PRODUCTION else None,
        env_file_encoding="utf-8",
    )


print(ENVIRONMENT)
config = Settings()
print(config)
