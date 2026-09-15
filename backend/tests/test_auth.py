"""Tests for Authentication API."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.database import init_db

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()
    yield

client = TestClient(app)


def test_login_success():
    """Verify valid credentials return JWT token and user profile."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@salesai.com",
            "password": "salesai123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@salesai.com"
    assert data["user"]["role"] == "admin"


def test_login_invalid_password():
    """Verify incorrect password returns 401 Unauthorized."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@salesai.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_invalid_email():
    """Verify unknown email returns 401 Unauthorized."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "stranger@otherdomain.com",
            "password": "salesai123",
        },
    )
    assert response.status_code == 401


def test_get_current_user_profile():
    """Verify /api/auth/me returns current user profile when authenticated with JWT."""
    # 1. Login to get token
    login_res = client.post(
        "/api/auth/login",
        json={"email": "admin@salesai.com", "password": "salesai123"},
    )
    token = login_res.json()["access_token"]

    # 2. Get profile with Bearer header
    me_res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    user = me_res.json()
    assert user["email"] == "admin@salesai.com"
    assert user["role"] == "admin"


def test_get_current_user_unauthorized():
    """Verify /api/auth/me rejects request without token."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_logout():
    """Verify /api/auth/logout succeeds."""
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert "Logged out successfully" in response.json()["message"]


def test_customer_registration_and_login():
    """Verify customer can register an account, get token, and then log in with it."""
    import uuid
    unique_email = f"customer_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "CustomerSecure123!"

    # 1. Register new customer
    reg_res = client.post(
        "/api/auth/register",
        json={
            "name": "Sarah Connor",
            "email": unique_email,
            "password": pwd,
        },
    )
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["name"] == "Sarah Connor"
    assert reg_data["user"]["email"] == unique_email
    assert reg_data["user"]["role"] == "member"

    # 2. Prevent duplicate registration with same email
    dup_res = client.post(
        "/api/auth/register",
        json={
            "name": "Another Name",
            "email": unique_email,
            "password": "anotherpassword",
        },
    )
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 3. Log in with registered customer credentials
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": unique_email,
            "password": pwd,
        },
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    token = login_data["access_token"]
    assert login_data["user"]["name"] == "Sarah Connor"

    # 4. Verify /me endpoint with customer's JWT token
    me_res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == unique_email
    assert me_res.json()["name"] == "Sarah Connor"

    # 5. Wrong password for customer returns 401
    bad_login = client.post(
        "/api/auth/login",
        json={
            "email": unique_email,
            "password": "WrongPassword123",
        },
    )
    assert bad_login.status_code == 401

