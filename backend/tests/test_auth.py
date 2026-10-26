from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import SESSION_COOKIE
from app.core.security import JWT_ALGORITHM
from app.models import User

PASSWORD = "password123"


def signup(client: TestClient, email: str = "a@example.com", password: str = PASSWORD, nickname: str = "alice"):
    return client.post("/api/auth/signup", json={"email": email, "password": password, "nickname": nickname})


def login(client: TestClient, email: str = "a@example.com", password: str = PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def fields(response) -> dict[str, str]:
    return response.json()["detail"]["fields"]


# --- signup (spec 2.1) ---


def test_signup_creates_account(client: TestClient, db: Session) -> None:
    response = signup(client)

    assert response.status_code == 201
    assert response.json() == {"id": 1, "email": "a@example.com", "nickname": "alice"}
    stored = db.scalar(select(User))
    assert stored.password_hash != PASSWORD


def test_signup_trims_email_and_nickname_but_not_password(client: TestClient) -> None:
    response = signup(client, email="  a@example.com  ", nickname="  alice ", password=" pass word ")

    assert response.json()["email"] == "a@example.com"
    assert response.json()["nickname"] == "alice"
    assert login(client, password=" pass word ").status_code == 200
    assert login(client, password="pass word").status_code == 401


def test_signup_rejects_duplicate_email(client: TestClient) -> None:
    signup(client, nickname="first")
    response = signup(client, nickname="second")

    assert response.status_code == 409
    assert "email" in fields(response)


def test_signup_allows_email_differing_only_in_case(client: TestClient) -> None:
    assert signup(client, email="Abc@mail.com", nickname="upper").status_code == 201
    assert signup(client, email="abc@mail.com", nickname="lower").status_code == 201


@pytest.mark.parametrize("taken", ["Kim", "kim", "KIM"])
def test_signup_rejects_nickname_differing_only_in_case(client: TestClient, taken: str) -> None:
    signup(client, email="a@example.com", nickname="Kim")
    response = signup(client, email="b@example.com", nickname=taken)

    assert response.status_code == 409
    assert "nickname" in fields(response)


@pytest.mark.parametrize("email", ["", "   ", "abc", "abc@", "@example.com", "a b@example.com"])
def test_signup_rejects_invalid_email(client: TestClient, email: str) -> None:
    response = signup(client, email=email)

    assert response.status_code == 422
    assert "email" in fields(response)


@pytest.mark.parametrize(("length", "accepted"), [(7, False), (8, True), (64, True), (65, False)])
def test_signup_password_length_boundaries(client: TestClient, length: int, accepted: bool) -> None:
    response = signup(client, password="p" * length)

    assert (response.status_code == 201) is accepted
    if not accepted:
        assert "password" in fields(response)


@pytest.mark.parametrize(
    ("nickname", "accepted"),
    [("a", False), ("ab", True), ("a" * 20, True), ("a" * 21, False), ("홍길동_99", True),
     ("닉네임!", False), ("with space", False), ("   ", False)],
)
def test_signup_nickname_rules(client: TestClient, nickname: str, accepted: bool) -> None:
    response = signup(client, nickname=nickname)

    assert (response.status_code == 201) is accepted
    if not accepted:
        assert "nickname" in fields(response)


def test_signup_reports_every_invalid_field_at_once(client: TestClient) -> None:
    response = signup(client, email="bad", password="short", nickname="!")

    assert set(fields(response)) == {"email", "password", "nickname"}


# --- login, me, logout (spec 2.2) ---


def test_login_sets_http_only_cookie_and_me_returns_user(client: TestClient) -> None:
    signup(client)
    response = login(client)

    assert response.status_code == 200
    cookie_header = response.headers["set-cookie"]
    assert SESSION_COOKIE in cookie_header
    assert "httponly" in cookie_header.lower()
    assert "samesite=lax" in cookie_header.lower()
    assert "secure" in cookie_header.lower()
    assert client.get("/api/auth/me").json()["nickname"] == "alice"


@pytest.mark.parametrize(("email", "password"), [("a@example.com", "wrong-password"), ("nobody@example.com", PASSWORD)])
def test_login_failure_gives_one_message_for_wrong_email_or_password(
    client: TestClient, email: str, password: str
) -> None:
    signup(client)
    response = login(client, email=email, password=password)

    assert response.status_code == 401
    assert response.json()["detail"]["message"] == "이메일 또는 비밀번호가 올바르지 않습니다."
    assert SESSION_COOKIE not in client.cookies


def test_login_email_is_case_sensitive(client: TestClient) -> None:
    signup(client, email="Abc@mail.com")

    assert login(client, email="abc@mail.com").status_code == 401


def test_me_requires_login(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"]["message"] == "로그인이 필요합니다."


def test_logout_clears_login(client: TestClient) -> None:
    signup(client)
    login(client)

    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_tampered_token_is_rejected(client: TestClient) -> None:
    signup(client)
    wrong_secret = "not-the-real-secret-but-long-enough-for-hs256"
    forged = jwt.encode({"sub": "1", "exp": datetime.now(UTC) + timedelta(days=1)}, wrong_secret, algorithm=JWT_ALGORITHM)
    client.cookies.set(SESSION_COOKIE, forged)

    assert client.get("/api/auth/me").status_code == 401


def test_expired_token_is_rejected(client: TestClient) -> None:
    signup(client)
    expired = jwt.encode({"sub": "1", "exp": datetime.now(UTC) - timedelta(seconds=1)}, settings.secret_key, algorithm=JWT_ALGORITHM)
    client.cookies.set(SESSION_COOKIE, expired)

    assert client.get("/api/auth/me").status_code == 401


# --- nickname change (spec 2.3) ---


def change_nickname(client: TestClient, nickname: str):
    return client.patch("/api/users/me/nickname", json={"nickname": nickname})


def test_nickname_change_requires_login(client: TestClient) -> None:
    assert change_nickname(client, "newname").status_code == 401


def test_nickname_change_succeeds(client: TestClient) -> None:
    signup(client)
    login(client)
    response = change_nickname(client, "  newname ")

    assert response.status_code == 200
    assert response.json()["nickname"] == "newname"
    assert client.get("/api/auth/me").json()["nickname"] == "newname"


def test_nickname_change_to_own_name_in_other_case_is_allowed(client: TestClient) -> None:
    signup(client, nickname="kim")
    login(client)

    assert change_nickname(client, "KIM").json()["nickname"] == "KIM"


def test_nickname_change_rejects_taken_name_in_any_case(client: TestClient) -> None:
    signup(client, email="a@example.com", nickname="alice")
    signup(client, email="b@example.com", nickname="Bob")
    login(client, email="a@example.com")
    response = change_nickname(client, "bob")

    assert response.status_code == 409
    assert client.get("/api/auth/me").json()["nickname"] == "alice"


@pytest.mark.parametrize("nickname", ["a", "a" * 21, "닉네임!", "   "])
def test_nickname_change_rejects_invalid_names(client: TestClient, nickname: str) -> None:
    signup(client)
    login(client)
    response = change_nickname(client, nickname)

    assert response.status_code == 422
    assert client.get("/api/auth/me").json()["nickname"] == "alice"


def test_nickname_change_only_affects_logged_in_user(client: TestClient, db: Session) -> None:
    signup(client, email="a@example.com", nickname="alice")
    signup(client, email="b@example.com", nickname="bob")
    login(client, email="a@example.com")
    change_nickname(client, "alice2")

    nicknames = set(db.scalars(select(User.nickname)))
    assert nicknames == {"alice2", "bob"}
