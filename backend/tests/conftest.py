from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import build_engine, get_db
from app.main import app

BACKEND_DIR = Path(__file__).resolve().parents[1]


def migrate(url: str) -> None:
    """Build the schema the same way production does: by running the Alembic migrations."""
    config = Config(BACKEND_DIR / "alembic.ini")
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.attributes["database_url"] = url
    command.upgrade(config, "head")


@pytest.fixture
def database_url(tmp_path: Path) -> str:
    # A fresh SQLite file per test, so tests never touch database/buildlog.sqlite3.
    return f"sqlite:///{(tmp_path / 'test.sqlite3').as_posix()}"


@pytest.fixture
def engine(database_url: str) -> Iterator[Engine]:
    migrate(database_url)
    engine = build_engine(database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def client(engine: Engine) -> Iterator[TestClient]:
    """The real app, its database swapped for this test's temporary one."""
    make_session = sessionmaker(bind=engine)

    def test_db() -> Iterator[Session]:
        session = make_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = test_db
    # https: the login cookie is Secure, so a client would not send it back over plain http.
    with TestClient(app, base_url="https://testserver") as test_client:
        yield test_client
    app.dependency_overrides.clear()
