import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"


def register_user(email: str, full_name: str = "Test User"):
    return client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "testpass123",
            "full_name": full_name,
        },
    )


def verify_user(token: str):
    return client.post("/auth/verify", json={"token": token})


def login_user(email: str):
    return client.post(
        "/auth/login",
        data={"username": email, "password": "testpass123"},
    )


def make_verified_user(prefix: str, full_name: str = "Test User"):
    email = unique_email(prefix)
    register_response = register_user(email, full_name=full_name)
    assert register_response.status_code == 201
    verification_token = register_response.json()["verification_token"]
    verify_response = verify_user(verification_token)
    assert verify_response.status_code == 200
    login_response = login_user(email)
    assert login_response.status_code == 200
    return email, login_response.json()["access_token"]


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_register_returns_verification_token():
    response = register_user(unique_email("integrationtest"), full_name="Integration Test")
    assert response.status_code == 201
    assert "verification_token" in response.json()


def test_login_requires_verification():
    email = unique_email("unverified")
    register_response = register_user(email, full_name="Unverified User")
    assert register_response.status_code == 201
    response = login_user(email)
    assert response.status_code == 403


def test_login_and_wrong_password():
    email, _ = make_verified_user("logintest", full_name="Login Test")
    response = login_user(email)
    assert response.status_code == 200
    assert "access_token" in response.json()

    wrong_password_response = client.post(
        "/auth/login",
        data={"username": email, "password": "wrongpassword"},
    )
    assert wrong_password_response.status_code == 401


def test_profile_and_onboarding_flow():
    email, token = make_verified_user("profiletest", full_name="Profile Test")

    profile_response = client.get("/profile", headers=auth_headers(token))
    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == email

    update_response = client.patch(
        "/profile",
        json={"full_name": "Updated Name", "student_status": "admin"},
        headers=auth_headers(token),
    )
    assert update_response.status_code == 200
    assert update_response.json()["full_name"] == "Updated Name"
    assert update_response.json()["student_status"] == "admin"

    academic_year_response = client.patch(
        "/profile/academic-year",
        json={"academic_year": 3},
        headers=auth_headers(token),
    )
    assert academic_year_response.status_code == 200
    assert academic_year_response.json()["academic_year"] == 3

    onboarding_response = client.get("/onboarding/status", headers=auth_headers(token))
    assert onboarding_response.status_code == 200
    assert onboarding_response.json()["academic_year"] == 3


def test_protected_route_requires_auth_header():
    response = client.get("/profile")
    assert response.status_code == 401


def test_chat_persists_session_and_messages():
    _, token = make_verified_user("chattest", full_name="Chat Test")

    response = client.post(
        "/chat",
        json={"message": "Hello!"},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    payload = response.json()
    assert "session_id" in payload
    assert "response" in payload

    sessions_response = client.get("/chat/sessions", headers=auth_headers(token))
    assert sessions_response.status_code == 200
    assert len(sessions_response.json()) >= 1

    messages_response = client.get(
        f"/chat/sessions/{payload['session_id']}/messages",
        headers=auth_headers(token),
    )
    assert messages_response.status_code == 200
    assert len(messages_response.json()) == 2


def test_documents_admin_upload_and_list():
    email, token = make_verified_user("documentstest", full_name="Documents Test")

    profile_response = client.patch(
        "/profile",
        json={"student_status": "admin"},
        headers=auth_headers(token),
    )
    assert profile_response.status_code == 200

    upload_response = client.post(
        "/documents",
        json={"title": "Test Doc", "content": "Some content"},
        headers=auth_headers(token),
    )
    assert upload_response.status_code == 201
    assert upload_response.json()["title"] == "Test Doc"

    list_response = client.get("/documents", headers=auth_headers(token))
    assert list_response.status_code == 200
    assert any(document["title"] == "Test Doc" for document in list_response.json())


def test_documents_reject_non_admin():
    _, token = make_verified_user("documentsblocked", full_name="Blocked User")
    response = client.post(
        "/documents",
        json={"title": "Blocked Doc", "content": "Nope"},
        headers=auth_headers(token),
    )
    assert response.status_code == 403
