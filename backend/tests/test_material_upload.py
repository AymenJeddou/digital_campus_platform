import io
import sys
import types
import uuid
from unittest.mock import patch

import docx  # python-docx — used here only to build a real test fixture
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app.main import app

client = TestClient(app)


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"


def make_verified_user(prefix: str):
    email = unique_email(prefix)
    with patch("app.api.routes.auth.send_verification_email") as send_email_mock:
        register_response = client.post(
            "/auth/register",
            json={"email": email, "password": "testpass123", "full_name": "Test User"},
        )
    assert register_response.status_code == 201
    verification_token = send_email_mock.call_args.args[1]
    verify_response = client.post("/auth/verify", json={"token": verification_token})
    assert verify_response.status_code == 200
    login_response = client.post("/auth/login", data={"username": email, "password": "testpass123"})
    assert login_response.status_code == 200
    return email, login_response.json()["access_token"]


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def mock_ingestion_modules():
    """Same stub as test_courses.py / test_classroom.py — avoids a real
    sentence-transformers download or a real structure-aware chunker run."""
    fake_embeddings_module = types.ModuleType("ai.rag.embeddings")
    fake_embeddings_module.embed_texts = lambda texts, **kw: [[0.1] * 768 for _ in texts]
    fake_embeddings_module.embed_query = lambda q: [0.1] * 768
    return (
        patch(
            "app.services.course_ingestion._chunk_text",
            side_effect=lambda text, source, title: [{
                "chunk_id": "abc",
                "text": text,
                "title": title,
                "source": source,
                "page": 0,
                "category": "course_material",
            }],
        ),
        patch.dict(sys.modules, {"ai.rag.embeddings": fake_embeddings_module}),
    )


def make_test_pdf_bytes(text: str = "Chapitre 1 : Introduction aux limites.") -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 720, text)
    pdf.save()
    return buffer.getvalue()


def make_test_docx_bytes(text: str = "Chapitre 1 : Introduction aux limites.") -> bytes:
    buffer = io.BytesIO()
    document = docx.Document()
    document.add_paragraph(text)
    document.save(buffer)
    return buffer.getvalue()


def make_blank_pdf_bytes() -> bytes:
    buffer = io.BytesIO()
    canvas.Canvas(buffer).save()  # a page with no text on it at all
    return buffer.getvalue()


def create_course_and_enroll(token: str) -> str:
    """Tests here have no fixture course to enroll in via a seeded catalog,
    so create one directly through the DB — same shortcut used implicitly
    by relying on the manual-enroll endpoint elsewhere; here we go straight
    to the DB since there's no course-creation endpoint exposed to students."""
    from app.db.database import SessionLocal
    from app.models.models import Course

    db = SessionLocal()
    try:
        course = Course(name="Analyse Mathématique")
        db.add(course)
        db.commit()
        db.refresh(course)
        course_id = str(course.id)
    finally:
        db.close()

    enroll_response = client.post(
        "/courses/enroll", json={"course_id": course_id}, headers=auth_headers(token)
    )
    assert enroll_response.status_code == 201
    return course_id


def test_upload_pdf_material_is_ingested():
    _, token = make_verified_user("uploadpdf")
    course_id = create_course_and_enroll(token)

    chunk_patch, embed_patch = mock_ingestion_modules()
    with chunk_patch, embed_patch:
        response = client.post(
            f"/courses/{course_id}/materials/upload",
            headers=auth_headers(token),
            files={"file": ("cours1.pdf", make_test_pdf_bytes(), "application/pdf")},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["source"] == "upload"
    assert body["original_filename"] == "cours1.pdf"
    assert body["status"] == "ingested"
    assert body["chunk_count"] == 1


def test_upload_docx_material_is_ingested():
    _, token = make_verified_user("uploaddocx")
    course_id = create_course_and_enroll(token)

    chunk_patch, embed_patch = mock_ingestion_modules()
    with chunk_patch, embed_patch:
        response = client.post(
            f"/courses/{course_id}/materials/upload",
            headers=auth_headers(token),
            files={
                "file": (
                    "td2.docx",
                    make_test_docx_bytes(),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

    assert response.status_code == 201
    body = response.json()
    assert body["source"] == "upload"
    assert body["original_filename"] == "td2.docx"
    assert body["status"] == "ingested"


def test_upload_uses_custom_title_when_provided():
    _, token = make_verified_user("uploadtitle")
    course_id = create_course_and_enroll(token)

    chunk_patch, embed_patch = mock_ingestion_modules()
    with chunk_patch, embed_patch:
        response = client.post(
            f"/courses/{course_id}/materials/upload",
            headers=auth_headers(token),
            data={"title": "Chapitre 1 - Limites"},
            files={"file": ("scan.pdf", make_test_pdf_bytes(), "application/pdf")},
        )

    assert response.status_code == 201
    assert response.json()["title"] == "Chapitre 1 - Limites"


def test_upload_rejects_unsupported_file_type():
    _, token = make_verified_user("uploadbadtype")
    course_id = create_course_and_enroll(token)

    response = client.post(
        f"/courses/{course_id}/materials/upload",
        headers=auth_headers(token),
        files={"file": ("archive.zip", b"PK\x03\x04fake", "application/zip")},
    )
    assert response.status_code == 415


def test_upload_rejects_pdf_with_no_extractable_text():
    _, token = make_verified_user("uploadblankpdf")
    course_id = create_course_and_enroll(token)

    response = client.post(
        f"/courses/{course_id}/materials/upload",
        headers=auth_headers(token),
        files={"file": ("blank.pdf", make_blank_pdf_bytes(), "application/pdf")},
    )
    assert response.status_code == 422


def test_upload_rejects_empty_file():
    _, token = make_verified_user("uploademptyfile")
    course_id = create_course_and_enroll(token)

    response = client.post(
        f"/courses/{course_id}/materials/upload",
        headers=auth_headers(token),
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert response.status_code == 422


def test_upload_requires_enrollment():
    _, token = make_verified_user("uploadnotenrolled")
    from app.db.database import SessionLocal
    from app.models.models import Course

    db = SessionLocal()
    try:
        course = Course(name="Physique Quantique")
        db.add(course)
        db.commit()
        db.refresh(course)
        course_id = str(course.id)
    finally:
        db.close()

    response = client.post(
        f"/courses/{course_id}/materials/upload",
        headers=auth_headers(token),
        files={"file": ("notes.txt", b"some notes", "text/plain")},
    )
    assert response.status_code == 403


def test_uploaded_material_appears_in_course_detail():
    _, token = make_verified_user("uploaddetail")
    course_id = create_course_and_enroll(token)

    chunk_patch, embed_patch = mock_ingestion_modules()
    with chunk_patch, embed_patch:
        client.post(
            f"/courses/{course_id}/materials/upload",
            headers=auth_headers(token),
            files={"file": ("notes.txt", b"Some plain text notes.", "text/plain")},
        )

    detail = client.get(f"/courses/{course_id}", headers=auth_headers(token))
    assert detail.status_code == 200
    materials = detail.json()["materials"]
    assert len(materials) == 1
    assert materials[0]["source"] == "upload"
    assert materials[0]["original_filename"] == "notes.txt"
