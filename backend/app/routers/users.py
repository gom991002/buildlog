from fastapi import APIRouter, status
from sqlalchemy.exc import IntegrityError

from app.core.deps import CurrentUser, DbSession, field_errors
from app.schemas.user import NicknameUpdateRequest, UserResponse, nickname_error
from app.services.users import nickname_taken, to_response

router = APIRouter(prefix="/api/users", tags=["users"])


@router.patch("/me/nickname")
def change_nickname(body: NicknameUpdateRequest, user: CurrentUser, db: DbSession) -> UserResponse:
    """Only the logged-in user's own nickname can change: there is no user id in the path."""
    nickname = body.nickname.strip()
    if message := nickname_error(nickname):
        raise field_errors(status.HTTP_422_UNPROCESSABLE_CONTENT, {"nickname": message})
    if nickname_taken(db, nickname, except_user_id=user.id):
        raise field_errors(status.HTTP_409_CONFLICT, {"nickname": "이미 사용 중인 닉네임입니다."})

    user.nickname = nickname
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise field_errors(status.HTTP_409_CONFLICT, {"nickname": "이미 사용 중인 닉네임입니다."})
    return to_response(user)
