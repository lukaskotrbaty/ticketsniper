from sqlalchemy import Boolean, Column, Integer, String, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_verified = Column(Boolean, nullable=False, server_default='false')
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(), # Note: server_onupdate is preferred for PG, but onupdate works too
        server_onupdate=func.now(), # Explicitly using server_onupdate for PG
    )

    # Relationship to UserRouteSubscription
    subscriptions = relationship(
        "UserRouteSubscription", back_populates="user", cascade="all, delete-orphan"
    )
