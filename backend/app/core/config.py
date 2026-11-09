from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# buildlog/ (project root): .env and relative database paths are resolved from here.
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # hide_input_in_errors: a wrong DATABASE_URL may contain the password, so never echo it.
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env", extra="ignore", hide_input_in_errors=True
    )

    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 10080

    # Learning materials (plan.md section 10). Files live on disk; only metadata goes to Supabase.
    upload_dir: Path = PROJECT_ROOT / "backend" / "uploads"
    # AI summary of uploaded files. An empty key turns the summary off; uploads still work.
    openai_api_key: str = ""
    openai_model: str = "gpt-5.4-nano"

    @field_validator("database_url")
    @classmethod
    def _require_supabase(cls, value: str) -> str:
        # The server stores data in Supabase only; it never falls back to SQLite.
        if not value.strip().startswith(("postgresql://", "postgres://", "postgresql+psycopg://")):
            raise ValueError(
                ".env의 DATABASE_URL에 Supabase 주소를 넣어주세요 "
                "(Supabase > Connect > Session pooler, postgresql://로 시작). SQLite는 사용하지 않습니다."
            )
        return value.strip()


settings = Settings()
