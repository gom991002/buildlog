import re
from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.db.base import Base

NICKNAME_PATTERN = re.compile(r"^[가-힣A-Za-z0-9_]{2,20}$")


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Emails are compared exactly as entered, so letter case matters.
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    nickname: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    @validates("nickname")
    def _validate_nickname(self, _key: str, value: str) -> str:
        if not NICKNAME_PATTERN.fullmatch(value):
            raise ValueError("닉네임은 2~20자의 한글, 영문, 숫자, 밑줄만 사용할 수 있습니다.")
        return value


# Nicknames are unique regardless of English letter case ("Kim" and "kim" clash).
Index("uq_users_nickname_lower", func.lower(User.nickname), unique=True)
