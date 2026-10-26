from fastapi import FastAPI

from app.core.config import settings  # noqa: F401  # fail at startup if .env is missing required values

app = FastAPI(title="BuildLog API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "message": "BuildLog 서버가 동작 중입니다."}
