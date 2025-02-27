from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MTAA project 2025"
    backend_db_url: str
    db_user: str
    db_password: str
    db_name: str
    model_config = SettingsConfigDict(env_file=".env")


config = Settings()
