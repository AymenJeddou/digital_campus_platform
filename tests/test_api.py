import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ── Auth ──────────────────────────────────────────────────────────────────────

def test_register():
    response = client.post("/auth/register", json={
        "email": "integrationtest@example.com",
        "password": "testpass123",
        "full_name": "Integration Test"
    })
    assert response.status_code in [201, 400]  # 400 if already exists

def test_login():
    client.post("/auth/register", json={
        "email": "logintest@example.com",
        "password": "testpass123",
        "full_name": "Login Test"
    })
    response = client.post("/auth/login", data={
        "username": "logintest@example.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password():
    response = client.post("/auth/login", data={
        "username": "logintest@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

# ── Profile ───────────────────────────────────────────────────────────────────

def get_token():
    client.post("/auth/register", json={
        "email": "profiletest@example.com",
        "password": "testpass123",
        "full_name": "Profile Test"
    })
    response = client.post("/auth/login", data={
        "username": "profiletest@example.com",
        "password": "testpass123"
    })
    return response.json()["access_token"]

def test_get_profile():
    token = get_token()
    response = client.get("/profile", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "profiletest@example.com"

def test_update_profile():
    token = get_token()
    response = client.patch("/profile", json={"full_name": "Updated Name"},
                            headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_onboarding_status():
    token = get_token()
    response = client.get("/profile/onboarding/status",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "onboarding_completed" in response.json()

# ── Chat ──────────────────────────────────────────────────────────────────────

def test_send_message():
    token = get_token()
    response = client.post("/chat", json={"message": "Hello!"},
                           headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "session_id" in response.json()
    assert "response" in response.json()

# ── Documents ─────────────────────────────────────────────────────────────────

def test_upload_document():
    token = get_token()
    response = client.post("/documents", json={"title": "Test Doc", "content": "Some content"},
                           headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201

def test_list_documents():
    token = get_token()
    response = client.get("/documents", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
