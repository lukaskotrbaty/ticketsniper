from sqlalchemy import create_engine # Added for sync engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session # Added Session for sync type hint

from app.core.config import settings # Corrected import (relative to /code)

# Create the async engine
# pool_pre_ping=True helps detect disconnected connections
engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=False) # Set echo=True for debugging SQL

# Create the async session factory
# expire_on_commit=False prevents attributes from being expired after commit
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# --- Synchronous Setup (for Celery tasks needing sync access) ---
# Create the synchronous engine
# Need to replace 'asyncpg' with 'psycopg2' in the URL for the sync driver
sync_database_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")
engine_sync = create_engine(sync_database_url, pool_pre_ping=True, echo=False)

# Create the synchronous session factory
SyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine_sync
)
# --- End Synchronous Setup ---


# Dependency to get ASYNC DB session (will be used in API endpoints)
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
