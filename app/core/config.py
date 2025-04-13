from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MTAA project 2025"
    db_user: str
    db_password: str
    db_name: str
    db_host: str
    model_config = SettingsConfigDict(env_file=".env")
    testing: str | None


config = Settings()
