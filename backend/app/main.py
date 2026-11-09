from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings  # noqa: F401  # fail at startup if .env is missing required values
from app.models.material import MAX_FILE_SIZE
from app.routers import auth, materials, users
from app.services.materials import FILE_SIZE_RULE

# The largest file plus room for the title, memo and form boundaries.
MAX_UPLOAD_REQUEST_BYTES = MAX_FILE_SIZE + 1024 * 1024

app = FastAPI(title="BuildLog API")
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(materials.router)


@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    """Refuse an oversized upload before the server reads the body into a temporary file."""
    if request.method == "POST" and request.url.path == "/api/materials":
        length = request.headers.get("content-length", "")
        if not length.isdigit() or int(length) > MAX_UPLOAD_REQUEST_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": {"message": FILE_SIZE_RULE, "fields": {"file": FILE_SIZE_RULE}}},
            )
    return await call_next(request)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "message": "BuildLog 서버가 동작 중입니다."}
