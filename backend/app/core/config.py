from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# buildlog/ (project root): .env and relative database paths are resolved from here.
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 10080


settings = Settings()
