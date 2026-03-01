"""Auth service -- user registration, login, and JWT token management."""

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: uuid.UUID) -> str:
    """Create a JWT access token for the given user."""
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID:
    """Decode a JWT access token and return the user_id.

    Raises:
        HTTPException(401): If the token is invalid, expired, or malformed.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
        return uuid.UUID(user_id_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )


async def register_user(db: AsyncSession, username: str, password: str) -> User:
    """Register a new user account.

    Validates username length (3-30 chars) and password length (min 6 chars).
    Checks uniqueness on username_lower.

    Raises:
        HTTPException(400): If validation fails.
        HTTPException(409): If username is already taken.
    """
    # Validate username length.
    if len(username) < 3 or len(username) > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be between 3 and 30 characters",
        )

    # Validate password length.
    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters",
        )

    # Check uniqueness (case-insensitive).
    username_lower = username.lower()
    result = await db.execute(select(User).where(User.username_lower == username_lower))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken",
        )

    user = User(
        username=username,
        username_lower=username_lower,
        password_hash=hash_password(password),
    )
    db.add(user)
    await db.flush()

    return user


async def login_user(db: AsyncSession, username: str, password: str) -> User:
    """Authenticate a user by username and password.

    Raises:
        HTTPException(401): If the username does not exist or the password is wrong.
            Uses a generic message to avoid leaking whether the username exists.
    """
    result = await db.execute(select(User).where(User.username_lower == username.lower()))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    return user
