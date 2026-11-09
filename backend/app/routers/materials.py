from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, field_errors
from app.models import Material
from app.schemas.material import MaterialResponse, memo_error, title_error
from app.services.ai_summary import summarize
from app.services.materials import (
    FileRejected,
    check_file,
    clean_filename,
    file_path,
    remove_file,
    save_upload,
    to_response,
)

router = APIRouter(prefix="/api/materials", tags=["materials"])

NOT_FOUND = "자료를 찾을 수 없습니다."


def owned_material(db: DbSession, user: CurrentUser, material_id: int) -> Material:
    """Another user's material answers 404 like a missing one, so its existence stays hidden."""
    material = db.get(Material, material_id)
    if material is None or material.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail={"message": NOT_FOUND})
    return material


@router.post("", status_code=status.HTTP_201_CREATED)
def upload_material(
    user: CurrentUser,
    db: DbSession,
    title: Annotated[str, Form()] = "",
    memo: Annotated[str, Form()] = "",
    file: Annotated[UploadFile | None, File()] = None,
) -> MaterialResponse:
    """Save one file, ask OpenAI for a summary, then store the metadata with the summary."""
    title = title.strip()
    memo = memo.strip()
    errors = {
        field: message
        for field, message in (("title", title_error(title)), ("memo", memo_error(memo)))
        if message
    }
    if file is None or not file.filename:
        errors["file"] = "올릴 파일을 선택해 주세요."
    if errors:
        raise field_errors(status.HTTP_422_UNPROCESSABLE_CONTENT, errors)

    original_filename = clean_filename(file.filename)
    try:
        content_type = check_file(original_filename, file.file.read(16))
        file.file.seek(0)
        stored_filename, size = save_upload(file.file, content_type)
    except FileRejected as rejected:
        raise field_errors(status.HTTP_422_UNPROCESSABLE_CONTENT, {"file": str(rejected)})

    try:
        ai_status, ai_summary = summarize(file_path(stored_filename), content_type, title, memo or None)
        material = Material(
            user_id=user.id,
            title=title,
            memo=memo or None,
            original_filename=original_filename,
            stored_filename=stored_filename,
            content_type=content_type,
            file_size=size,
            ai_summary=ai_summary,
            ai_status=ai_status,
        )
        db.add(material)
        db.commit()
    except BaseException:
        # No row means no file: never leave a file nobody can see or delete.
        db.rollback()
        remove_file(stored_filename)
        raise
    return to_response(material)


@router.get("")
def list_materials(user: CurrentUser, db: DbSession) -> list[MaterialResponse]:
    """Only the logged-in user's materials, newest first."""
    materials = db.scalars(
        select(Material)
        .where(Material.user_id == user.id)
        .order_by(Material.created_at.desc(), Material.id.desc())
    )
    return [to_response(material) for material in materials]


@router.get("/{material_id}/file")
def material_file(material_id: int, user: CurrentUser, db: DbSession) -> FileResponse:
    """The original file, shown in the browser. Range requests let videos seek."""
    material = owned_material(db, user, material_id)
    path = file_path(material.stored_filename)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail={"message": "원본 파일이 없습니다."})
    return FileResponse(
        path,
        media_type=material.content_type,
        filename=material.original_filename,
        content_disposition_type="inline",
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"},
    )


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(material_id: int, user: CurrentUser, db: DbSession) -> Response:
    """Delete the row first: a leftover file is harmless, a row without its file is not."""
    material = owned_material(db, user, material_id)
    stored_filename = material.stored_filename
    db.delete(material)
    db.commit()
    remove_file(stored_filename)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
