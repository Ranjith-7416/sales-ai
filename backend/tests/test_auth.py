"""Tests for Authentication API."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

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
