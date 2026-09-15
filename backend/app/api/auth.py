"""Authentication API - JWT login, session verification and logout."""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
import secrets
import logging

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> UserResponse:
    """Verify and decode JWT token from Authorization Bearer header."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return UserResponse(
            id=payload.get("id", "user-admin-1"),
            name=payload.get("name", settings.ADMIN_NAME),
            email=email,
            role=payload.get("role", settings.ADMIN_ROLE),
        )
    except JWTError as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    """
    Authenticate user and return signed JWT token.
    Default credentials: admin@salesai.com / salesai123 (or configured in settings)
    """
    input_email = payload.email.strip().lower()
    input_pass = payload.password.strip()

    expected_email = settings.ADMIN_EMAIL.strip().lower()
    expected_pass = settings.ADMIN_PASSWORD.strip()

    email_matches = secrets.compare_digest(input_email, expected_email)
    pass_matches = secrets.compare_digest(input_pass, expected_pass)

    if not (email_matches and pass_matches):
        logger.warning(f"Failed login attempt for {input_email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Use demo credentials: admin@salesai.com / salesai123",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": expected_email,
        "id": "user-admin-1",
        "name": settings.ADMIN_NAME,
        "role": settings.ADMIN_ROLE,
    }
    token = create_access_token(data=token_data, expires_delta=expires_delta)

    logger.info(f"User {expected_email} logged in successfully")
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=int(expires_delta.total_seconds()),
        user=UserResponse(
            id="user-admin-1",
            name=settings.ADMIN_NAME,
            email=expected_email,
            role=settings.ADMIN_ROLE,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: UserResponse = Depends(get_current_user)):
    """Retrieve current authenticated user profile."""
    return current_user


@router.post("/logout")
async def logout():
    """Invalidate client session."""
    return {"message": "Logged out successfully"}
