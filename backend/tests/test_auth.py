"""Tests for Authentication API."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.database import init_db

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()
    from app.services.cache_service import get_cache_service
    from app.database import SessionLocal
    from app.models import User
    cache = get_cache_service()
    cache.in_memory_cache.clear()

    db = SessionLocal()
    try:
        db.query(User).filter(User.email == "admin@salesai.com").delete()
        db.commit()
    finally:
        db.close()

    yield

    db = SessionLocal()
    try:
        db.query(User).filter(User.email == "admin@salesai.com").delete()
        db.commit()
    finally:
        db.close()

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


def test_login_character_variant_and_reset_password(monkeypatch):
    """Verify single/double character variant (e.g. Ranjiith <-> Ranjith) and reset-password endpoint."""
    import uuid
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "ENABLE_DEV_OTP", True)

    email = f"variant_{uuid.uuid4().hex[:8]}@example.com"
    registered_pass = "Ranjith_37"
    variant_pass = "Ranjiith_37"

    # Register with 1 'i'
    res = client.post(
        "/api/auth/register",
        json={"name": "Ranjith Kumar", "email": email, "password": registered_pass},
    )
    assert res.status_code == 201

    # Login with 2 'i's (common mobile keyboard double-tap)
    login_variant = client.post(
        "/api/auth/login",
        json={"email": email, "password": variant_pass},
    )
    assert login_variant.status_code == 200
    assert "access_token" in login_variant.json()

    # Request OTP via forgot-password
    forgot_res = client.post(
        "/api/auth/forgot-password",
        json={"email": email},
    )
    assert forgot_res.status_code == 200
    forgot_data = forgot_res.json()
    assert forgot_data["success"] is True
    assert "If an account exists" in forgot_data["message"]
    otp_code = forgot_data.get("dev_otp")
    assert otp_code is not None

    # Test invalid OTP rejected
    bad_reset = client.post(
        "/api/auth/reset-password",
        json={"email": email, "otp_code": "000000", "new_password": "NewSecretPassword99!"},
    )
    assert bad_reset.status_code == 400
    assert "Invalid verification code" in bad_reset.json()["detail"]

    # Reset password with valid OTP
    reset_res = client.post(
        "/api/auth/reset-password",
        json={"email": email, "otp_code": otp_code, "new_password": "NewSecretPassword99!"},
    )
    assert reset_res.status_code == 200
    assert "access_token" in reset_res.json()

    # Verify code cannot be reused
    reused_reset = client.post(
        "/api/auth/reset-password",
        json={"email": email, "otp_code": otp_code, "new_password": "AnotherPassword123!"},
    )
    assert reused_reset.status_code == 400

    # Login with new password
    new_login = client.post(
        "/api/auth/login",
        json={"email": email, "password": "NewSecretPassword99!"},
    )
    assert new_login.status_code == 200


def test_forgot_password_generic_response_no_enumeration(monkeypatch):
    """Verify forgot-password returns identical 200 generic responses for both existing and unknown emails."""
    import uuid
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "ENABLE_DEV_OTP", True)

    existing_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={"name": "Alice Bob", "email": existing_email, "password": "Password123!"},
    )

    # 1. Existing account
    res_existing = client.post(
        "/api/auth/forgot-password",
        json={"email": existing_email},
    )
    assert res_existing.status_code == 200
    assert "If an account exists" in res_existing.json()["message"]
    assert res_existing.json()["dev_otp"] is not None

    # 2. Non-existent account (returns same 200 message; dev_otp is strictly None)
    unknown_email = f"unknown_{uuid.uuid4().hex[:8]}@example.com"
    res_unknown = client.post(
        "/api/auth/forgot-password",
        json={"email": unknown_email},
    )
    assert res_unknown.status_code == 200
    assert res_unknown.json()["message"] == res_existing.json()["message"]
    assert res_unknown.json()["dev_otp"] is None


def test_dev_otp_unavailable_in_production(monkeypatch):
    """Verify dev_otp is strictly omitted in production environments."""
    import uuid
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "ENABLE_DEV_OTP", True)  # Even if flag is set, production blocks it

    email = f"prod_test_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={"name": "Prod User", "email": email, "password": "Password123!"},
    )

    res = client.post(
        "/api/auth/forgot-password",
        json={"email": email},
    )
    assert res.status_code == 200
    assert res.json().get("dev_otp") is None


def test_dev_otp_unavailable_when_flag_disabled(monkeypatch):
    """Verify dev_otp is omitted when ENABLE_DEV_OTP is False in development."""
    import uuid
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "ENABLE_DEV_OTP", False)

    email = f"dev_disabled_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={"name": "Dev User", "email": email, "password": "Password123!"},
    )

    res = client.post(
        "/api/auth/forgot-password",
        json={"email": email},
    )
    assert res.status_code == 200
    assert res.json().get("dev_otp") is None


def test_reset_password_with_expired_otp_fails(monkeypatch):
    """Verify expired OTP code is rejected."""
    import uuid
    from datetime import datetime, timedelta
    from app.database import SessionLocal
    from app.models import PasswordResetToken
    from app.api.auth import hash_otp_code

    email = f"expired_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={"name": "Expired Test", "email": email, "password": "Password123!"},
    )

    otp_code = "654321"
    db = SessionLocal()
    try:
        token = PasswordResetToken(
            email=email,
            otp_code=hash_otp_code(otp_code, email),
            expires_at=datetime.utcnow() - timedelta(minutes=1),  # Expired
            is_used=False,
            attempts=0,
        )
        db.add(token)
        db.commit()
    finally:
        db.close()

    res = client.post(
        "/api/auth/reset-password",
        json={"email": email, "otp_code": otp_code, "new_password": "NewPassword123!"},
    )
    assert res.status_code == 400
    assert "expired" in res.json()["detail"].lower()


def test_reset_password_too_many_attempts_locks_otp(monkeypatch):
    """Verify 5 incorrect attempts invalidate the OTP."""
    import uuid
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "ENABLE_DEV_OTP", True)

    email = f"bruteforce_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={"name": "Brute Test", "email": email, "password": "Password123!"},
    )

    forgot_res = client.post("/api/auth/forgot-password", json={"email": email})
    correct_otp = forgot_res.json()["dev_otp"]

    # 4 invalid attempts
    for i in range(4):
        bad_res = client.post(
            "/api/auth/reset-password",
            json={"email": email, "otp_code": f"00000{i}", "new_password": "NewPassword123!"},
        )
        assert bad_res.status_code == 400
        assert "Invalid verification code" in bad_res.json()["detail"]

    # 5th invalid attempt invalidates token
    bad_res_5 = client.post(
        "/api/auth/reset-password",
        json={"email": email, "otp_code": "000005", "new_password": "NewPassword123!"},
    )
    assert bad_res_5.status_code == 400

    # 6th attempt (even with correct OTP) is now rejected because token is locked
    locked_res = client.post(
        "/api/auth/reset-password",
        json={"email": email, "otp_code": correct_otp, "new_password": "NewPassword123!"},
    )
    assert locked_res.status_code == 400
    assert "invalidated" in locked_res.json()["detail"].lower() or "no active" in locked_res.json()["detail"].lower()


def test_request_new_otp_invalidates_previous_otps(monkeypatch):
    """Verify requesting a new OTP invalidates the previous unexpired OTP."""
    import uuid
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "ENABLE_DEV_OTP", True)

    email = f"superseded_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={"name": "Superseded Test", "email": email, "password": "Password123!"},
    )

    # Request OTP 1
    res1 = client.post("/api/auth/forgot-password", json={"email": email})
    otp1 = res1.json()["dev_otp"]

    # Request OTP 2
    res2 = client.post("/api/auth/forgot-password", json={"email": email})
    otp2 = res2.json()["dev_otp"]

    # Attempting to use OTP 1 fails
    res_otp1 = client.post(
        "/api/auth/reset-password",
        json={"email": email, "otp_code": otp1, "new_password": "NewPassword123!"},
    )
    assert res_otp1.status_code == 400

    # Using OTP 2 succeeds
    res_otp2 = client.post(
        "/api/auth/reset-password",
        json={"email": email, "otp_code": otp2, "new_password": "NewPassword123!"},
    )
    assert res_otp2.status_code == 200


def test_reset_password_weak_password_rejected(monkeypatch):
    """Verify backend enforces minimum password length during reset."""
    import uuid
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "ENABLE_DEV_OTP", True)

    email = f"weak_pass_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={"name": "Weak Pass User", "email": email, "password": "Password123!"},
    )

    forgot_res = client.post("/api/auth/forgot-password", json={"email": email})
    otp_code = forgot_res.json()["dev_otp"]

    # 1. Pydantic schema validation rejects length < 6 (HTTP 422)
    res_short = client.post(
        "/api/auth/reset-password",
        json={"email": email, "otp_code": otp_code, "new_password": "123"},
    )
    assert res_short.status_code in (400, 422)

    # 2. Custom backend validator rejects whitespace padding (HTTP 400)
    res_whitespace = client.post(
        "/api/auth/reset-password",
        json={"email": email, "otp_code": otp_code, "new_password": "   123   "},
    )
    assert res_whitespace.status_code == 400
    assert "at least 8 characters" in res_whitespace.json()["detail"]


def test_simplified_reset_password_success():
    """Verify simplified reset-password without OTP resets password and enables login."""
    import uuid
    email = f"simplified_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={"name": "Simplified User", "email": email, "password": "InitialPassword123!"},
    )

    # Simplified reset passing email and new password >= 8 characters (no OTP)
    reset_res = client.post(
        "/api/auth/reset-password",
        json={"email": email, "new_password": "CalmWaterResetPass123!"},
    )
    assert reset_res.status_code == 200
    data = reset_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == email

    # Verify old password no longer works
    old_login = client.post(
        "/api/auth/login",
        json={"email": email, "password": "InitialPassword123!"},
    )
    assert old_login.status_code == 401

    # Verify new password logs in successfully
    new_login = client.post(
        "/api/auth/login",
        json={"email": email, "password": "CalmWaterResetPass123!"},
    )
    assert new_login.status_code == 200


def test_simplified_reset_password_too_short():
    """Verify passwords shorter than 8 characters are rejected."""
    import uuid
    email = f"short_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={"name": "Short Test", "email": email, "password": "ValidInitialPass123!"},
    )

    res = client.post(
        "/api/auth/reset-password",
        json={"email": email, "new_password": "short7!"},  # 7 characters
    )
    assert res.status_code in (400, 422)


def test_simplified_reset_password_unauthenticated_no_email():
    """Verify unauthenticated reset without email is rejected (Requirement 8)."""
    res = client.post(
        "/api/auth/reset-password",
        json={"new_password": "SecurePassword123!"},
    )
    assert res.status_code == 400
    assert "account email is required" in res.json()["detail"].lower()


def test_simplified_reset_password_authenticated_bearer():
    """Verify authenticated user can reset password using Bearer token without passing email."""
    import uuid
    email = f"bearer_reset_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = client.post(
        "/api/auth/register",
        json={"name": "Bearer User", "email": email, "password": "OriginalPass123!"},
    )
    token = reg_res.json()["access_token"]

    # Reset with Bearer token
    reset_res = client.post(
        "/api/auth/reset-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"new_password": "BrandNewPassword123!"},
    )
    assert reset_res.status_code == 200

    # Log in with new password
    login_res = client.post(
        "/api/auth/login",
        json={"email": email, "password": "BrandNewPassword123!"},
    )
    assert login_res.status_code == 200


def test_admin_account_reset_and_login():
    """Verify admin account can reset password and subsequently log in with new password."""
    new_admin_pass = "SuperSecretAdminWater2026!"
    res = client.post(
        "/api/auth/reset-password",
        json={"email": "admin@salesai.com", "new_password": new_admin_pass},
    )
    assert res.status_code == 200
    assert res.json()["user"]["email"] == "admin@salesai.com"

    # Verify login with updated password
    login_res = client.post(
        "/api/auth/login",
        json={"email": "admin@salesai.com", "password": new_admin_pass},
    )
    assert login_res.status_code == 200
    assert login_res.json()["user"]["role"] == "admin"




