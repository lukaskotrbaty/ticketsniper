from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
import secrets
import redis.asyncio as redis

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings # Corrected import (relative to /code)
from app.schemas.token import TokenData # Corrected import (relative to /code)

# Password Hashing Setup
# Using bcrypt as the default hashing scheme
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

# JWT Token Creation and Verification

def create_access_token(subject: Union[str, Any], expires_delta: timedelta | None = None) -> str:
    """Creates a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_email_confirmation_token(email: str) -> str:
    """Creates a JWT specifically for email confirmation."""
    expires_delta = timedelta(minutes=settings.EMAIL_CONFIRMATION_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "exp": expire,
        "sub": email,
        "scope": "email_confirmation", # Add scope to differentiate from access tokens
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str, expected_scope: str | None = None) -> TokenData | None:
    """
    Verifies a JWT token and optionally checks its scope.
    Returns TokenData if valid, None otherwise.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str | None = payload.get("sub")
        if email is None:
            return None # Or raise exception

        if expected_scope:
            scope = payload.get("scope")
            if scope != expected_scope:
                return None # Or raise exception for invalid scope

        token_data = TokenData(sub=email)
        return token_data

    except JWTError:
        # Could log the error here
        return None # Or raise specific exception


# --- Password Reset Token Handling (using Redis) ---

# Prefix pro klíče v Redis, aby se oddělily od ostatních dat
RESET_TOKEN_PREFIX = "reset_token:"

async def create_password_reset_token(redis_client: redis.Redis, user_id: int) -> str:
    """
    Generates a secure password reset token, stores it in Redis with expiration,
    and returns the token.
    """
    token = secrets.token_urlsafe(32)
    redis_key = f"{RESET_TOKEN_PREFIX}{token}"
    expire_seconds = settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES * 60

    # Store the user_id associated with the token, with an expiration time
    await redis_client.setex(redis_key, expire_seconds, str(user_id))
    return token

async def validate_password_reset_token(redis_client: redis.Redis, token: str) -> Optional[int]:
    """
    Validates the password reset token by checking its existence in Redis.
    Returns the user_id if valid, None otherwise.
    """
    redis_key = f"{RESET_TOKEN_PREFIX}{token}"
    user_id_str = await redis_client.get(redis_key)

    if user_id_str:
        try:
            return int(user_id_str)
        except (ValueError, TypeError):
             # Should not happen if stored correctly, but handle defensively
            return None
    return None

async def invalidate_password_reset_token(redis_client: redis.Redis, token: str) -> None:
    """
    Invalidates/deletes the password reset token from Redis.
    """
    redis_key = f"{RESET_TOKEN_PREFIX}{token}"
    await redis_client.delete(redis_key)
