import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.config import settings
from app.database import get_session
from app.models.user import User


security = HTTPBearer()


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256.

    A unique random salt is generated for every password.
    The stored format is:

        salt_hex:password_hash_hex
    """

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        310_000,
    )

    return f"{salt.hex()}:{password_hash.hex()}"


def verify_password(
    password: str,
    stored_hash: str,
) -> bool:
    """
    Verify a plain-text password against the stored PBKDF2 hash.
    """

    try:
        salt_hex, hash_hex = stored_hash.split(":")

        salt = bytes.fromhex(salt_hex)

        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            310_000,
        )

        return hmac.compare_digest(
            calculated_hash.hex(),
            hash_hex,
        )

    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int) -> str:
    """
    Create a JWT access token for the authenticated user.
    """

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> User:
    """
    Validate the JWT access token and return the current user.
    """

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )

        user_id = int(payload["sub"])

    except (
        jwt.InvalidTokenError,
        KeyError,
        ValueError,
        TypeError,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    user = session.get(User, user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return user