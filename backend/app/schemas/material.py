from datetime import datetime

from pydantic import BaseModel

from app.models.material import MEMO_MAX, TITLE_MAX


class MaterialResponse(BaseModel):
    id: int
    title: str
    memo: str | None
    original_filename: str
    content_type: str
    file_size: int
    ai_summary: str | None
    ai_status: str
    created_at: datetime
    # Where the screen opens the original file; the stored file name is never exposed.
    file_url: str


def title_error(title: str) -> str | None:
    """Checks an already-trimmed title."""
    if title == "":
        return "제목을 입력해 주세요."
    if len(title) > TITLE_MAX:
        return f"제목은 1~{TITLE_MAX}자로 입력해 주세요."
    return None


def memo_error(memo: str) -> str | None:
    """Checks an already-trimmed memo; an empty memo is allowed."""
    if len(memo) > MEMO_MAX:
        return f"메모는 {MEMO_MAX:,}자 이하로 입력해 주세요."
    return None
