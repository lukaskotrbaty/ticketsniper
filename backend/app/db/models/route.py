from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    TIMESTAMP,
    UniqueConstraint,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base

# Define an Enum for route status
class RouteStatusEnum(enum.Enum):
    MONITORING = "MONITORING"
    FOUND = "FOUND"
    EXPIRED = "EXPIRED"

class MonitoredRoute(Base):
    __tablename__ = "monitored_routes"

    id = Column(Integer, primary_key=True, index=True)
    regiojet_route_id = Column(String, nullable=False) 
    from_location_id = Column(String, nullable=False)
    from_location_type = Column(String, nullable=False)
    to_location_id = Column(String, nullable=False)
    to_location_type = Column(String, nullable=False)
    departure_datetime = Column(TIMESTAMP(timezone=True), nullable=False)
    arrival_datetime = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(Enum(RouteStatusEnum, name="route_status_enum", create_type=True), nullable=False, default=RouteStatusEnum.MONITORING, server_default=RouteStatusEnum.MONITORING.value)
    last_checked_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    # Relationship to UserRouteSubscription
    subscribers = relationship(
        "UserRouteSubscription", back_populates="route", cascade="all, delete-orphan"
    )

    # Index for worker queries and unique constraint for the route segment
    __table_args__ = (
        Index("ix_monitored_routes_status_departure", "status", "departure_datetime"),
        UniqueConstraint('regiojet_route_id', 'from_location_id', 'to_location_id', name='uq_monitored_route_segment'),
    )


class UserRouteSubscription(Base):
    __tablename__ = "user_route_subscriptions"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    route_id = Column(Integer, ForeignKey("monitored_routes.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    route = relationship("MonitoredRoute", back_populates="subscribers")
