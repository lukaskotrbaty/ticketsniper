import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import crud_user
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

pytestmark = pytest.mark.asyncio

async def test_create_user(db_session: AsyncSession):
    """
    Test creating a new user in the database.
    """
    email = "test@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password, password_confirm=password)
    
    created_user = await crud_user.create_user(db=db_session, user_in=user_in)
    
    assert created_user.email == email
    assert created_user.hashed_password is not None
    assert created_user.is_verified is False
    assert created_user.id is not None

async def test_get_user_by_email(db_session: AsyncSession):
    """
    Test retrieving a user by their email.
    """
    email = "get_user@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password, password_confirm=password)
    await crud_user.create_user(db=db_session, user_in=user_in)
    
    retrieved_user = await crud_user.get_user_by_email(db=db_session, email=email)
    
    assert retrieved_user is not None
    assert retrieved_user.email == email

async def test_get_user_by_email_not_found(db_session: AsyncSession):
    """
    Test that None is returned for a non-existent email.
    """
    retrieved_user = await crud_user.get_user_by_email(db=db_session, email="nonexistent@example.com")
    assert retrieved_user is None
