import redis.asyncio as redis
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.db import crud, models
from app.db.session import get_db

# Define the OAuth2 scheme, pointing to the login endpoint
# The path should match the final path after including routers
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
        db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> models.User:
    """
    Dependency to get the current user from the JWT token.
    Raises HTTPException 401 if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = security.verify_token(token)
    if not token_data or not token_data.sub:
        raise credentials_exception

    user = await crud.get_user_by_email(db, email=token_data.sub)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
        current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Dependency to get the current *active* (verified) user.
    Raises HTTPException 400 if the user is not verified.
    """
    if not current_user.is_verified:
        raise HTTPException(status_code=400, detail="Inactive user / Email not verified")
    return current_user


# Redis Dependency
# It's often better to manage the pool globally (e.g., in main.py lifespan)
# but for simplicity here, we create a connection per request.
# Consider optimizing with a connection pool for production.
async def get_redis_client() -> redis.Redis:
    """
    Dependency to get an asynchronous Redis client instance.
    """
    try:
        # Create a new connection for each request (can be inefficient)
        # A better approach uses a connection pool managed in app lifespan
        client = await redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        yield client
        # Ensure the connection is closed after the request
        await client.close()
    except redis.RedisError as e:
        # Log the error e
        print(f"Could not connect to Redis: {e}")  # Basic logging
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to Redis service."
        )


# HTTP Client Dependency
async def get_http_client() -> httpx.AsyncClient:
    """
    Dependency that provides an httpx.AsyncClient for making HTTP requests.
    The client's lifecycle is managed automatically by the 'async with' block.
    """
    async with httpx.AsyncClient() as client:
        yield client
