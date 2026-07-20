import sys
import types
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"


def make_verified_user(prefix: str):
    email = unique_email(prefix)
    with patch("app.api.routes.auth.send_verification_email") as send_email_mock:
        register_response = client.post(
            "/auth/register",
            json={"email": email, "password": "Testpass123!", "full_name": "Test User"},
        )
    assert register_response.status_code == 201
    verification_token = send_email_mock.call_args.args[1]
    verify_response = client.post("/auth/verify", json={"token": verification_token})
    assert verify_response.status_code == 200
    login_response = client.post("/auth/login", data={"username": email, "password": "Testpass123!"})
    assert login_response.status_code == 200
    return email, login_response.json()["access_token"]


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def mock_ingestion_modules():
    """Same stub as test_courses.py — avoids a real sentence-transformers
    download / a real structure-aware chunker run in tests."""
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


def fake_classroom_course(course_id="ext-course-1", name="Algèbre 1"):
    return {"id": course_id, "name": name, "section": "MATH101"}


def fake_coursework(item_id="ext-work-1", title="Devoir 1"):
    return {"id": item_id, "title": title, "description": "Résoudre les exercices 1 à 5.", "materials": []}


def test_classroom_status_defaults_to_disconnected():
    _, token = make_verified_user("classroomstatus")
    response = client.get("/courses/classroom/status", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["connected"] is False


def test_classroom_authorize_returns_signed_state_url():
    _, token = make_verified_user("classroomauth")
    with patch("app.api.routes.courses.classroom_client.build_authorization_url", return_value="https://accounts.google.com/mock?state=abc"):
        response = client.post("/courses/classroom/authorize", headers=auth_headers(token))
    assert response.status_code == 200
    assert "authorization_url" in response.json()


def test_classroom_callback_rejects_invalid_state():
    response = client.get(
        "/courses/classroom/callback",
        params={"code": "x", "state": "not-a-real-token"},
        follow_redirects=False,
    )
    assert response.status_code in (302, 307)
    assert "classroom=error" in response.headers["location"]


def test_classroom_callback_connects_account_with_valid_state():
    from app.api.routes.courses import _sign_state

    _, token = make_verified_user("classroomcallback")
    # Recover the student id via /profile-equivalent: decode isn't exposed,
    # so just sign a state directly using the same helper the route uses,
    # scoped to a freshly created user fetched via the DB.
    from app.db.database import SessionLocal
    from app.models.models import Student

    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.email.like("classroomcallback-%")).order_by(Student.enrollment_date.desc()).first()
        state = _sign_state(student.id)
        student_id = student.id
    finally:
        db.close()

    fake_token_set = types.SimpleNamespace(
        access_token="fake-access", refresh_token="fake-refresh", expires_at=9999999999.0, scope="classroom"
    )
    with patch("app.api.routes.courses.classroom_client.exchange_code_for_tokens", return_value=fake_token_set):
        response = client.get(
            "/courses/classroom/callback",
            params={"code": "fake-code", "state": state},
            follow_redirects=False,
        )
    assert response.status_code in (302, 307)
    assert "classroom=connected" in response.headers["location"]

    status_response = client.get("/courses/classroom/status", headers=auth_headers(token))
    assert status_response.json()["connected"] is True

    from app.models.models import GoogleClassroomAccount
    db = SessionLocal()
    try:
        account = db.query(GoogleClassroomAccount).filter(GoogleClassroomAccount.student_id == student_id).first()
        assert account is not None
        assert account.access_token != "fake-access"  # stored encrypted, not in plaintext
    finally:
        db.close()


def test_classroom_sync_requires_connection():
    _, token = make_verified_user("classroomsyncnoconn")
    response = client.post("/courses/classroom/sync", headers=auth_headers(token))
    assert response.status_code == 400


def test_classroom_sync_creates_courses_and_ingests_materials():
    from app.api.routes.courses import _sign_state
    from app.db.database import SessionLocal
    from app.models.models import GoogleClassroomAccount, Student
    from app.services.token_crypto import encrypt_token

    _, token = make_verified_user("classroomsync")

    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.email.like("classroomsync-%")).order_by(Student.enrollment_date.desc()).first()
        account = GoogleClassroomAccount(
            student_id=student.id,
            access_token=encrypt_token("fake-access"),
            refresh_token=encrypt_token("fake-refresh"),
            token_expires_at=9999999999.0,
        )
        db.add(account)
        db.commit()
    finally:
        db.close()

    chunk_patch, embed_patch = mock_ingestion_modules()
    with chunk_patch, embed_patch, \
         patch("app.services.classroom_sync.classroom_client.list_courses", return_value=[fake_classroom_course()]), \
         patch("app.services.classroom_sync.classroom_client.list_coursework", return_value=[fake_coursework()]), \
         patch("app.services.classroom_sync.classroom_client.list_coursework_materials", return_value=[]), \
         patch("app.services.classroom_sync.classroom_client.list_announcements", return_value=[]):
        response = client.post("/courses/classroom/sync", headers=auth_headers(token))

    assert response.status_code == 200
    body = response.json()
    assert body["courses_synced"] == 1
    assert body["materials_synced"] == 1

    mine = client.get("/courses/mine", headers=auth_headers(token))
    assert mine.status_code == 200
    synced = [c for c in mine.json() if c["source"] == "google_classroom"]
    assert len(synced) == 1
    assert synced[0]["material_count"] == 1
    assert synced[0]["name"] == "Algèbre 1"


def test_classroom_sync_is_idempotent_on_repeat_runs():
    """Running sync twice should update, not duplicate, the same material."""
    from app.db.database import SessionLocal
    from app.models.models import GoogleClassroomAccount, Student
    from app.services.token_crypto import encrypt_token

    _, token = make_verified_user("classroomresync")

    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.email.like("classroomresync-%")).order_by(Student.enrollment_date.desc()).first()
        account = GoogleClassroomAccount(
            student_id=student.id,
            access_token=encrypt_token("fake-access"),
            refresh_token=encrypt_token("fake-refresh"),
            token_expires_at=9999999999.0,
        )
        db.add(account)
        db.commit()
    finally:
        db.close()

    chunk_patch, embed_patch = mock_ingestion_modules()
    with chunk_patch, embed_patch, \
         patch("app.services.classroom_sync.classroom_client.list_courses", return_value=[fake_classroom_course()]), \
         patch("app.services.classroom_sync.classroom_client.list_coursework", return_value=[fake_coursework()]), \
         patch("app.services.classroom_sync.classroom_client.list_coursework_materials", return_value=[]), \
         patch("app.services.classroom_sync.classroom_client.list_announcements", return_value=[]):
        client.post("/courses/classroom/sync", headers=auth_headers(token))
        second = client.post("/courses/classroom/sync", headers=auth_headers(token))

    assert second.status_code == 200
    mine = client.get("/courses/mine", headers=auth_headers(token))
    synced = [c for c in mine.json() if c["source"] == "google_classroom"]
    assert len(synced) == 1
    assert synced[0]["material_count"] == 1  # not 2 — same external_id was updated in place


def test_classroom_disconnect_removes_account():
    from app.db.database import SessionLocal
    from app.models.models import GoogleClassroomAccount, Student
    from app.services.token_crypto import encrypt_token

    _, token = make_verified_user("classroomdisconnect")

    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.email.like("classroomdisconnect-%")).order_by(Student.enrollment_date.desc()).first()
        account = GoogleClassroomAccount(
            student_id=student.id,
            access_token=encrypt_token("fake-access"),
            refresh_token=encrypt_token("fake-refresh"),
            token_expires_at=9999999999.0,
        )
        db.add(account)
        db.commit()
    finally:
        db.close()

    disconnect = client.delete("/courses/classroom", headers=auth_headers(token))
    assert disconnect.status_code == 204

    status_response = client.get("/courses/classroom/status", headers=auth_headers(token))
    assert status_response.json()["connected"] is False

    sync_after_disconnect = client.post("/courses/classroom/sync", headers=auth_headers(token))
    assert sync_after_disconnect.status_code == 400
