from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.deps import SESSION_COOKIE, CurrentUser, DbSession, field_errors
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.user import (
    LoginRequest,
    SignupRequest,
    UserResponse,
    email_error,
    nickname_error,
    password_error,
)
from app.services.users import nickname_taken, to_response

router = APIRouter(prefix="/api/auth", tags=["auth"])

LOGIN_FAILED = "이메일 또는 비밀번호가 올바르지 않습니다."


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, db: DbSession) -> UserResponse:
    email = body.email.strip()
    nickname = body.nickname.strip()

    errors = {
        field: message
        for field, message in (
            ("email", email_error(email)),
            ("password", password_error(body.password)),
            ("nickname", nickname_error(nickname)),
        )
        if message
    }
    if errors:
        raise field_errors(status.HTTP_422_UNPROCESSABLE_CONTENT, errors)

    conflicts = {}
    if db.scalar(select(User.id).where(User.email == email)) is not None:
        conflicts["email"] = "이미 사용 중인 이메일입니다."
    if nickname_taken(db, nickname):
        conflicts["nickname"] = "이미 사용 중인 닉네임입니다."
    if conflicts:
        raise field_errors(status.HTTP_409_CONFLICT, conflicts)

    user = User(email=email, nickname=nickname, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Someone took the email or nickname between the check and the save.
        db.rollback()
        raise field_errors(status.HTTP_409_CONFLICT, {"email": "이미 사용 중인 이메일 또는 닉네임입니다."})
    return to_response(user)


@router.post("/login")
def login(body: LoginRequest, response: Response, db: DbSession) -> UserResponse:
    user = db.scalar(select(User).where(User.email == body.email.strip()))
    # One message for a wrong email and a wrong password, so nobody can probe which emails exist.
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={"message": LOGIN_FAILED})

    response.set_cookie(
        SESSION_COOKIE,
        create_access_token(user.id),
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        samesite="lax",
        # HTTPS only. Chrome, Edge and Firefox still accept it on http://localhost; Safari does not.
        secure=True,
        path="/",
    )
    return to_response(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="lax", secure=True)


@router.get("/me")
def me(user: CurrentUser) -> UserResponse:
    return to_response(user)
