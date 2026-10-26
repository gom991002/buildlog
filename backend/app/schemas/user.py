from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel

from app.models.user import NICKNAME_PATTERN, NICKNAME_RULE

PASSWORD_MIN = 8
PASSWORD_MAX = 64
EMAIL_MAX = 254


class SignupRequest(BaseModel):
    email: str
    password: str
    nickname: str


class LoginRequest(BaseModel):
    email: str
    password: str


class NicknameUpdateRequest(BaseModel):
    nickname: str


class UserResponse(BaseModel):
    id: int
    email: str
    nickname: str


def email_error(email: str) -> str | None:
    """Checks an already-trimmed email; the stored value stays exactly as entered."""
    if email == "":
        return "이메일을 입력해 주세요."
    if len(email) > EMAIL_MAX:
        return "올바른 이메일 주소를 입력해 주세요."
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return "올바른 이메일 주소를 입력해 주세요."
    return None


def password_error(password: str) -> str | None:
    """Passwords are checked as entered: no trimming."""
    if not PASSWORD_MIN <= len(password) <= PASSWORD_MAX:
        return f"비밀번호는 {PASSWORD_MIN}~{PASSWORD_MAX}자로 입력해 주세요."
    return None


def nickname_error(nickname: str) -> str | None:
    """Checks an already-trimmed nickname."""
    if nickname == "":
        return "닉네임을 입력해 주세요."
    if not NICKNAME_PATTERN.fullmatch(nickname):
        return NICKNAME_RULE
    return None
