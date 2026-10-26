from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import PROJECT_ROOT, settings


def resolve_database_url(url: str) -> str:
    """Make a relative SQLite path point inside the project root, wherever the server is started."""
    parsed = make_url(url)
    if parsed.get_backend_name() != "sqlite" or parsed.database in (None, "", ":memory:"):
        return url
    path = Path(parsed.database)
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return parsed.set(database=str(path)).render_as_string(hide_password=False)


def build_engine(url: str) -> Engine:
    engine = create_engine(resolve_database_url(url))
    if engine.dialect.name == "sqlite":
        # SQLite ignores foreign keys unless this is turned on for every connection.
        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = build_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
