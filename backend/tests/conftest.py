import asyncio
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.main import app
from app.db.base import Base
from app.db.session import get_db

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency override for getting a DB session in tests.
    """
    async with TestingSessionLocal() as session:
        yield session

# Apply the override for the application instance
app.dependency_overrides[get_db] = override_get_db_session

@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for the session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """
    Create database tables before any tests run, and drop them after.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture to get a database session for a test.
    This fixture clears all data after each test to ensure test isolation.
    """
    async with TestingSessionLocal() as session:
        yield session
        # Clean up all data after the test
        await session.rollback()
        # Manually delete all data from tables to ensure isolation
        async with engine.begin() as conn:
            # Delete in reverse order to handle foreign key constraints
            await conn.execute(text("DELETE FROM user_route_subscriptions"))
            await conn.execute(text("DELETE FROM monitored_routes")) 
            await conn.execute(text("DELETE FROM users"))
            await conn.commit()

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture to get an httpx.AsyncClient for making API requests.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
