from typing import List # Added
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session as SyncSession # Added for sync tasks
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload # Added joinedload

from app.db.models.user import User
from app.db.models.route import UserRouteSubscription # Added
from app.schemas.user import UserCreate
from app.core.security import get_password_hash


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Gets a user by their ID."""
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Gets a user by their email address."""
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Creates a new user."""
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        is_verified=False # Explicitly set, though default is false
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def activate_user(db: AsyncSession, db_user: User) -> User:
    """Activates a user by setting is_verified to True (Async version)."""
    if not db_user.is_verified:
        db_user.is_verified = True
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
    return db_user


async def update_user_password(db: AsyncSession, *, db_user: User, new_hashed_password: str) -> User:
    """Updates a user's password."""
    db_user.hashed_password = new_hashed_password
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
