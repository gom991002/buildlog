from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User
from app.schemas.user import UserResponse


def nickname_taken(db: Session, nickname: str, except_user_id: int | None = None) -> bool:
    """Nicknames clash regardless of English letter case."""
    query = select(User.id).where(func.lower(User.nickname) == nickname.lower())
    if except_user_id is not None:
        query = query.where(User.id != except_user_id)
    return db.scalar(query) is not None


def to_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, nickname=user.nickname)
