import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.db.session import build_engine
from app.models import User


def make_user(email: str = "a@example.com", nickname: str = "tester", password: str = "password123") -> User:
    return User(email=email, nickname=nickname, password_hash=hash_password(password))


def test_users_with_different_email_and_nickname_are_saved(db: Session) -> None:
    db.add_all([make_user("a@example.com", "alice"), make_user("b@example.com", "bob")])
    db.commit()

    assert db.scalar(select(User).where(User.nickname == "alice")).email == "a@example.com"
    assert len(db.scalars(select(User)).all()) == 2


def test_created_at_is_set_automatically(db: Session) -> None:
    user = make_user()
    db.add(user)
    db.commit()

    assert user.created_at is not None


def test_duplicate_email_is_rejected(db: Session) -> None:
    db.add(make_user("same@example.com", "first"))
    db.commit()

    db.add(make_user("same@example.com", "second"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_email_differing_only_in_case_is_a_different_account(db: Session) -> None:
    db.add_all([make_user("Abc@mail.com", "upper"), make_user("abc@mail.com", "lower")])
    db.commit()

    assert len(db.scalars(select(User)).all()) == 2


def test_duplicate_nickname_is_rejected(db: Session) -> None:
    db.add(make_user("a@example.com", "Kim"))
    db.commit()

    db.add(make_user("b@example.com", "Kim"))
    with pytest.raises(IntegrityError):
        db.commit()


@pytest.mark.parametrize("nickname", ["kim", "KIM", "kIm"])
def test_nickname_differing_only_in_case_is_rejected(db: Session, nickname: str) -> None:
    db.add(make_user("a@example.com", "Kim"))
    db.commit()

    db.add(make_user("b@example.com", nickname))
    with pytest.raises(IntegrityError):
        db.commit()


def test_nickname_is_stored_as_entered(db: Session) -> None:
    db.add(make_user(nickname="KimDev"))
    db.commit()

    assert db.scalar(select(User.nickname)) == "KimDev"


@pytest.mark.parametrize("nickname", ["가나", "ab", "a" * 20, "홍길동_99", "Dev_Kim1"])
def test_valid_nicknames_are_accepted(nickname: str) -> None:
    assert make_user(nickname=nickname).nickname == nickname


@pytest.mark.parametrize(
    "nickname",
    ["a", "a" * 21, "", "닉네임!", "with space", "dash-name", "ㄱㄴ", "이모지😀"],
)
def test_invalid_nicknames_are_rejected(nickname: str) -> None:
    with pytest.raises(ValueError):
        make_user(nickname=nickname)


def test_password_is_not_stored_as_plain_text(db: Session) -> None:
    db.add(make_user(password="password123"))
    db.commit()

    stored = db.scalar(select(User.password_hash))
    assert stored != "password123"
    assert "password123" not in stored
    assert verify_password("password123", stored)
    assert not verify_password("wrong-password", stored)


def test_users_remain_after_reconnecting(database_url: str, db: Session) -> None:
    db.add(make_user("keep@example.com", "keeper"))
    db.commit()
    db.close()

    # A brand-new engine is what a server restart looks like to the database.
    fresh_engine = build_engine(database_url)
    with Session(fresh_engine) as fresh:
        assert fresh.scalar(select(User.email)) == "keep@example.com"
    fresh_engine.dispose()
