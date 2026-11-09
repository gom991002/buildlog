import io
from pathlib import Path

import av
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Material
from app.services import ai_summary

PASSWORD = "password123"
MIB = 1024 * 1024
MP4_HEAD = b"\x00\x00\x00\x18ftypmp42"


def login_as(client: TestClient, name: str = "alice") -> None:
    """Sign up (first time) and log in; the client then carries that user's cookie."""
    email = f"{name}@example.com"
    client.post("/api/auth/signup", json={"email": email, "password": PASSWORD, "nickname": name})
    assert client.post("/api/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200


def png_bytes(color=(30, 120, 220)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (40, 30), color).save(buffer, format="PNG")
    return buffer.getvalue()


def jpeg_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (40, 30), (200, 40, 40)).save(buffer, format="JPEG")
    return buffer.getvalue()


def mp4_bytes(tmp_path: Path, seconds: int = 2, fps: int = 10) -> bytes:
    path = tmp_path / "sample.mp4"
    with av.open(str(path), "w", format="mp4") as output:
        stream = output.add_stream("mpeg4", rate=fps)
        stream.width, stream.height, stream.pix_fmt = 64, 48, "yuv420p"
        for index in range(seconds * fps):
            frame = av.VideoFrame.from_image(Image.new("RGB", (64, 48), (index * 12 % 256, 80, 160)))
            for packet in stream.encode(frame):
                output.mux(packet)
        for packet in stream.encode():
            output.mux(packet)
    return path.read_bytes()


def upload(client: TestClient, title="REST 정리", memo="", filename="note.png", content=None, mime="image/png"):
    files = {"file": (filename, png_bytes() if content is None else content, mime)}
    return client.post("/api/materials", data={"title": title, "memo": memo}, files=files)


def fields(response) -> dict[str, str]:
    return response.json()["detail"]["fields"]


# --- upload ---


def test_upload_png_saves_file_and_row(client: TestClient, db: Session, upload_dir: Path) -> None:
    login_as(client)
    response = upload(client, title="  REST 정리  ", memo="  요청 구조  ")

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "REST 정리"
    assert body["memo"] == "요청 구조"
    assert body["original_filename"] == "note.png"
    assert body["content_type"] == "image/png"
    assert body["file_url"] == f"/api/materials/{body['id']}/file"
    assert body["ai_status"] == "disabled" and body["ai_summary"] is None
    assert "stored_filename" not in body

    stored = db.scalar(select(Material))
    assert stored.file_size == len(png_bytes())
    assert (upload_dir / stored.stored_filename).read_bytes() == png_bytes()
    assert "note" not in stored.stored_filename


@pytest.mark.parametrize("filename", ["photo.jpg", "photo.JPEG"])
def test_upload_jpeg(client: TestClient, filename: str) -> None:
    login_as(client)
    response = upload(client, filename=filename, content=jpeg_bytes(), mime="image/jpeg")
    assert response.status_code == 201
    assert response.json()["content_type"] == "image/jpeg"


def test_upload_mp4(client: TestClient, tmp_path: Path) -> None:
    login_as(client)
    response = upload(client, filename="demo.mp4", content=mp4_bytes(tmp_path), mime="video/mp4")
    assert response.status_code == 201
    assert response.json()["content_type"] == "video/mp4"


def test_title_boundaries(client: TestClient) -> None:
    login_as(client)
    assert upload(client, title="가").status_code == 201
    assert upload(client, title="가" * 100).status_code == 201
    assert fields(upload(client, title="가" * 101))["title"]
    assert fields(upload(client, title="   "))["title"]


def test_memo_is_optional_and_limited(client: TestClient) -> None:
    login_as(client)
    assert upload(client, memo="   ").json()["memo"] is None
    assert upload(client, memo="메" * 1000).status_code == 201
    assert fields(upload(client, memo="메" * 1001))["memo"]


def test_upload_without_file(client: TestClient) -> None:
    login_as(client)
    response = client.post("/api/materials", data={"title": "제목"})
    assert response.status_code == 422
    assert fields(response)["file"]


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("anim.gif", b"GIF89a" + b"0" * 20),  # type not allowed
        ("fake.png", b"GIF89a" + b"0" * 20),  # name says PNG, content is not
        ("image.mp4", None),  # PNG content named .mp4
        ("noext", None),
    ],
)
def test_upload_rejects_other_types(client: TestClient, db: Session, upload_dir: Path, filename, content) -> None:
    login_as(client)
    response = upload(client, filename=filename, content=content)

    assert response.status_code == 422
    assert fields(response)["file"]
    assert db.scalar(select(Material)) is None
    assert not upload_dir.exists() or not any(upload_dir.iterdir())


def test_image_size_limit(client: TestClient, upload_dir: Path) -> None:
    login_as(client)
    header = png_bytes()
    assert upload(client, content=header + b"0" * (5 * MIB - len(header))).status_code == 201
    response = upload(client, content=header + b"0" * (5 * MIB - len(header) + 1))
    assert response.status_code == 422
    assert fields(response)["file"]
    assert len(list(upload_dir.iterdir())) == 1  # the rejected partial file was removed


def test_video_size_limit(client: TestClient) -> None:
    login_as(client)
    assert upload(client, filename="v.mp4", content=MP4_HEAD + b"0" * (30 * MIB - len(MP4_HEAD)), mime="video/mp4").status_code == 201
    response = upload(client, filename="v.mp4", content=MP4_HEAD + b"0" * (30 * MIB - len(MP4_HEAD) + 1), mime="video/mp4")
    assert response.status_code == 422


def test_oversized_request_is_refused_before_reading(client: TestClient) -> None:
    login_as(client)
    response = upload(client, filename="v.mp4", content=MP4_HEAD + b"0" * (32 * MIB), mime="video/mp4")
    assert response.status_code == 413
    assert fields(response)["file"]


def test_folder_in_filename_is_dropped(client: TestClient) -> None:
    login_as(client)
    response = upload(client, filename="..\\..\\secret\\note.png")
    assert response.json()["original_filename"] == "note.png"


def test_row_failure_removes_saved_file(client: TestClient, upload_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    login_as(client)

    def broken(*_args):
        raise RuntimeError("database down")

    monkeypatch.setattr("app.routers.materials.summarize", broken)
    with pytest.raises(RuntimeError):
        upload(client)
    assert not any(upload_dir.iterdir())


# --- login and ownership ---


def test_every_request_needs_login(client: TestClient) -> None:
    assert upload(client).status_code == 401
    assert client.get("/api/materials").status_code == 401
    assert client.get("/api/materials/1/file").status_code == 401
    assert client.delete("/api/materials/1").status_code == 401


def test_list_shows_only_own_materials_newest_first(client: TestClient) -> None:
    login_as(client, "alice")
    upload(client, title="첫 번째")
    upload(client, title="두 번째")
    login_as(client, "bob")
    upload(client, title="밥의 자료")

    assert [m["title"] for m in client.get("/api/materials").json()] == ["밥의 자료"]
    login_as(client, "alice")
    assert [m["title"] for m in client.get("/api/materials").json()] == ["두 번째", "첫 번째"]


def test_view_original_file(client: TestClient) -> None:
    login_as(client)
    material = upload(client, filename="한글 이름.png").json()

    response = client.get(material["file_url"])
    assert response.status_code == 200
    assert response.content == png_bytes()
    assert response.headers["content-type"] == "image/png"
    assert response.headers["content-disposition"].startswith("inline")
    assert response.headers["x-content-type-options"] == "nosniff"


def test_video_supports_range_requests(client: TestClient, tmp_path: Path) -> None:
    login_as(client)
    video = mp4_bytes(tmp_path)
    material = upload(client, filename="demo.mp4", content=video, mime="video/mp4").json()

    response = client.get(material["file_url"], headers={"Range": "bytes=0-9"})
    assert response.status_code == 206
    assert response.content == video[:10]


def test_other_user_cannot_view_or_delete(client: TestClient, upload_dir: Path) -> None:
    login_as(client, "alice")
    material = upload(client).json()
    login_as(client, "bob")

    assert client.get(material["file_url"]).status_code == 404
    assert client.delete(f"/api/materials/{material['id']}").status_code == 404
    assert len(list(upload_dir.iterdir())) == 1


def test_delete_removes_row_and_file(client: TestClient, db: Session, upload_dir: Path) -> None:
    login_as(client)
    material = upload(client).json()

    assert client.delete(f"/api/materials/{material['id']}").status_code == 204
    assert db.scalar(select(Material)) is None
    assert not any(upload_dir.iterdir())
    assert client.get(material["file_url"]).status_code == 404
    assert client.delete(f"/api/materials/{material['id']}").status_code == 404


# --- AI summary (OpenAI is never called; the request itself is replaced) ---


@pytest.fixture
def fake_openai(monkeypatch: pytest.MonkeyPatch) -> list:
    calls = []

    def fake_request(prompt, images):
        calls.append((prompt, images))
        return "  REST 요청 구조를 정리한 이미지입니다.  "

    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(ai_summary, "request_summary", fake_request)
    return calls


def test_summary_is_saved_with_the_material(client: TestClient, db: Session, fake_openai: list) -> None:
    login_as(client)
    response = upload(client, title="REST 정리", memo="복습용")

    assert response.json()["ai_status"] == "done"
    assert response.json()["ai_summary"] == "REST 요청 구조를 정리한 이미지입니다."
    assert db.scalar(select(Material)).ai_summary == "REST 요청 구조를 정리한 이미지입니다."
    prompt, images = fake_openai[0]
    assert "REST 정리" in prompt and "복습용" in prompt
    assert len(images) == 1 and images[0][0].startswith("data:image/jpeg;base64,")


def test_video_is_summarized_from_frames(client: TestClient, tmp_path: Path, fake_openai: list) -> None:
    login_as(client)
    response = upload(client, filename="demo.mp4", content=mp4_bytes(tmp_path), mime="video/mp4")

    assert response.json()["ai_status"] == "done"
    _prompt, images = fake_openai[0]
    assert len(images) == ai_summary.VIDEO_FRAME_COUNT
    assert all(detail == "low" for _url, detail in images)


def test_failed_summary_keeps_the_upload(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def failing(_prompt, _images):
        raise TimeoutError("OpenAI did not answer")

    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(ai_summary, "request_summary", failing)
    login_as(client)
    response = upload(client)

    assert response.status_code == 201
    assert response.json()["ai_status"] == "failed"
    assert response.json()["ai_summary"] is None


def test_unreadable_video_fails_summary_but_keeps_upload(client: TestClient, fake_openai: list) -> None:
    login_as(client)
    response = upload(client, filename="broken.mp4", content=MP4_HEAD + b"0" * 100, mime="video/mp4")

    assert response.status_code == 201
    assert response.json()["ai_status"] == "failed"
    assert fake_openai == []


def test_long_summary_is_cut(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(ai_summary, "request_summary", lambda _p, _i: "가" * 3000)
    login_as(client)
    assert len(upload(client).json()["ai_summary"]) == 2000
