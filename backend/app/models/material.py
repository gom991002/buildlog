from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.user import utc_now

TITLE_MAX = 100
MEMO_MAX = 1000
ORIGINAL_FILENAME_MAX = 255
AI_SUMMARY_MAX = 2000

# content type -> (stored file extension, size limit in bytes)
FILE_RULES = {
    "image/png": (".png", 5 * 1024 * 1024),
    "image/jpeg": (".jpg", 5 * 1024 * 1024),
    "video/mp4": (".mp4", 30 * 1024 * 1024),
}
MAX_FILE_SIZE = max(limit for _ext, limit in FILE_RULES.values())

AI_DONE = "done"
AI_FAILED = "failed"
AI_DISABLED = "disabled"


class Material(Base):
    """A private learning material: one uploaded file plus what the owner wrote about it.

    The file itself is stored under settings.upload_dir; only its metadata is in this table.
    """

    __tablename__ = "materials"
    __table_args__ = (
        CheckConstraint(
            "content_type IN ('image/png', 'image/jpeg', 'video/mp4')", name="content_type"
        ),
        CheckConstraint(f"file_size > 0 AND file_size <= {MAX_FILE_SIZE}", name="file_size"),
        CheckConstraint(
            f"ai_status IN ('{AI_DONE}', '{AI_FAILED}', '{AI_DISABLED}')", name="ai_status"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(TITLE_MAX))
    memo: Mapped[str | None] = mapped_column(String(MEMO_MAX))
    original_filename: Mapped[str] = mapped_column(String(ORIGINAL_FILENAME_MAX))
    # Server-made random name, so a user's file name never becomes a path on disk.
    stored_filename: Mapped[str] = mapped_column(String(64), unique=True)
    content_type: Mapped[str] = mapped_column(String(20))
    file_size: Mapped[int] = mapped_column(Integer)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# The list screen reads one user's materials, newest first.
Index("ix_materials_user_id_created_at", Material.user_id, Material.created_at)
