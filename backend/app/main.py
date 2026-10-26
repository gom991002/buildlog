from fastapi import FastAPI

from app.core.config import settings  # noqa: F401  # fail at startup if .env is missing required values
from app.routers import auth, users

app = FastAPI(title="BuildLog API")
app.include_router(auth.router)
app.include_router(users.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "message": "BuildLog 서버가 동작 중입니다."}
