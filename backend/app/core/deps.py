from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import read_access_token
from app.db.session import get_db
from app.models import User

SESSION_COOKIE = "buildlog_session"

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(request: Request, db: DbSession) -> User:
    """The logged-in user, or 401 for a missing, tampered or expired login cookie."""
    token = request.cookies.get(SESSION_COOKIE)
    user_id = read_access_token(token) if token else None
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={"message": "로그인이 필요합니다."})
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def field_errors(status_code: int, fields: dict[str, str]) -> HTTPException:
    """An error the screen can show next to each input: {"detail": {"message", "fields"}}."""
    return HTTPException(status_code, detail={"message": next(iter(fields.values())), "fields": fields})
