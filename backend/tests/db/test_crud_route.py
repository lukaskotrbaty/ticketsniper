import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker, Session as SyncSession
from sqlalchemy import create_engine
import datetime
import uuid

from app.db.crud import crud_route, crud_user
from app.db.models.route import MonitoredRoute, UserRouteSubscription, RouteStatusEnum
from app.schemas.route import RouteMonitorRequest
from app.schemas.user import UserCreate
from app.db.models.user import User
from app.db.base import Base

# Use a separate sync engine for sync session tests
sync_engine = create_engine("sqlite:///:memory:")
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

@pytest.fixture(scope="function")
def sync_db_session():
    """Fixture for a synchronous database session for Celery-related tests."""
    Base.metadata.create_all(bind=sync_engine)
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=sync_engine)


@pytest.fixture
def sample_route_request() -> RouteMonitorRequest:
    """Provides a sample RouteMonitorRequest for testing."""
    return RouteMonitorRequest(
        regiojet_route_id="12345",
        from_location_id="100",
        from_location_type="STATION",
        to_location_id="200",
        to_location_type="STATION",
        departure_datetime=datetime.datetime.now(datetime.timezone.utc),
        arrival_datetime=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2),
    )

def generate_unique_email():
    """Generate a unique email for each test."""
    return f"test-{uuid.uuid4()}@example.com"

@pytest.mark.asyncio
async def test_get_or_create_monitored_route_creates_new(db_session: AsyncSession, sample_route_request: RouteMonitorRequest):
    """Test creating a new monitored route when it doesn't exist."""
    route = await crud_route.get_or_create_monitored_route(db=db_session, route_in=sample_route_request)
    assert route is not None
    assert route.regiojet_route_id == sample_route_request.regiojet_route_id
    assert route.status == RouteStatusEnum.MONITORING

@pytest.mark.asyncio
async def test_get_or_create_monitored_route_returns_existing(db_session: AsyncSession, sample_route_request: RouteMonitorRequest):
    """Test returning an existing monitored route."""
    # Create it once
    created_route = await crud_route.get_or_create_monitored_route(db=db_session, route_in=sample_route_request)
    
    # Try to get it again
    route = await crud_route.get_or_create_monitored_route(db=db_session, route_in=sample_route_request)
    assert route is not None
    assert route.id == created_route.id

@pytest.mark.asyncio
async def test_get_or_create_monitored_route_reactivates_inactive(db_session: AsyncSession, sample_route_request: RouteMonitorRequest):
    """Test that an existing, inactive route gets reactivated."""
    # Create it first
    initial_route = await crud_route.get_or_create_monitored_route(db=db_session, route_in=sample_route_request)
    
    # Manually set it to inactive
    initial_route.status = RouteStatusEnum.FOUND
    db_session.add(initial_route)
    await db_session.commit()
    await db_session.refresh(initial_route)
    assert initial_route.status == RouteStatusEnum.FOUND

    # Call the function again
    reactivated_route = await crud_route.get_or_create_monitored_route(db=db_session, route_in=sample_route_request)
    assert reactivated_route.id == initial_route.id
    assert reactivated_route.status == RouteStatusEnum.MONITORING

@pytest.mark.asyncio
async def test_create_user_subscription(db_session: AsyncSession, sample_route_request: RouteMonitorRequest):
    """Test creating a user subscription to a route."""
    user_in = UserCreate(email=generate_unique_email(), password="password123", password_confirm="password123")
    test_user = await crud_user.create_user(db_session, user_in=user_in)
    created_route = await crud_route.get_or_create_monitored_route(db=db_session, route_in=sample_route_request)
    
    # Get fresh IDs via refresh to avoid lazy loading issues
    await db_session.refresh(test_user)
    await db_session.refresh(created_route)
    user_id = test_user.id
    route_id = created_route.id

    subscription = await crud_route.create_user_subscription(db=db_session, user_id=user_id, route_id=route_id)
    await db_session.refresh(subscription)
    assert subscription is not None
    assert subscription.user_id == user_id
    assert subscription.route_id == route_id

@pytest.mark.asyncio
async def test_create_user_subscription_already_exists(db_session: AsyncSession, sample_route_request: RouteMonitorRequest):
    """Test that creating an existing subscription returns the existing one."""
    user_in = UserCreate(email=generate_unique_email(), password="password123", password_confirm="password123")
    test_user = await crud_user.create_user(db_session, user_in=user_in)
    created_route = await crud_route.get_or_create_monitored_route(db=db_session, route_in=sample_route_request)

    # Get fresh IDs via refresh to avoid lazy loading issues
    await db_session.refresh(test_user)
    await db_session.refresh(created_route)
    user_id = test_user.id
    route_id = created_route.id

    sub1 = await crud_route.create_user_subscription(db=db_session, user_id=user_id, route_id=route_id)
    await db_session.refresh(sub1)
    sub2 = await crud_route.create_user_subscription(db=db_session, user_id=user_id, route_id=route_id)
    await db_session.refresh(sub2)
    assert sub1.user_id == sub2.user_id and sub1.route_id == sub2.route_id

@pytest.mark.asyncio
async def test_get_user_subscriptions(db_session: AsyncSession, sample_route_request: RouteMonitorRequest):
    """Test retrieving all subscriptions for a user."""
    user_in = UserCreate(email=generate_unique_email(), password="password123", password_confirm="password123")
    test_user = await crud_user.create_user(db_session, user_in=user_in)
    created_route = await crud_route.get_or_create_monitored_route(db=db_session, route_in=sample_route_request)

    # Get fresh IDs via refresh to avoid lazy loading issues
    await db_session.refresh(test_user)
    await db_session.refresh(created_route)
    user_id = test_user.id
    route_id = created_route.id

    subscription = await crud_route.create_user_subscription(db=db_session, user_id=user_id, route_id=route_id)
    await db_session.refresh(subscription)
    subscriptions = await crud_route.get_user_subscriptions(db=db_session, user_id=user_id)
    assert len(subscriptions) == 1
    # Avoid lazy loading by comparing IDs instead of accessing related objects
    assert subscriptions[0].route_id == route_id

@pytest.mark.asyncio
async def test_delete_user_subscription(db_session: AsyncSession, sample_route_request: RouteMonitorRequest):
    """Test deleting a user subscription."""
    user_in = UserCreate(email=generate_unique_email(), password="password123", password_confirm="password123")
    test_user = await crud_user.create_user(db_session, user_in=user_in)
    created_route = await crud_route.get_or_create_monitored_route(db=db_session, route_in=sample_route_request)

    # Get fresh IDs via refresh to avoid lazy loading issues
    await db_session.refresh(test_user)
    await db_session.refresh(created_route)
    user_id = test_user.id
    route_id = created_route.id

    subscription = await crud_route.create_user_subscription(db=db_session, user_id=user_id, route_id=route_id)
    await db_session.refresh(subscription)
    
    # Verify subscription was created
    initial_count = await crud_route.count_subscriptions_for_route(db=db_session, route_id=route_id)
    assert initial_count == 1
    
    # Delete subscription
    deleted = await crud_route.delete_user_subscription(db=db_session, user_id=user_id, route_id=route_id)
    assert deleted is True
    
    # Verify subscription was deleted
    final_count = await crud_route.count_subscriptions_for_route(db=db_session, route_id=route_id)
    assert final_count == 0

@pytest.mark.asyncio
async def test_delete_monitored_route(db_session: AsyncSession, sample_route_request: RouteMonitorRequest):
    """Test deleting a monitored route."""
    created_route = await crud_route.get_or_create_monitored_route(db=db_session, route_in=sample_route_request)
    deleted = await crud_route.delete_monitored_route(db=db_session, route_id=created_route.id)
    assert deleted is True
    route = await crud_route.get_monitored_route_by_id(db=db_session, route_id=created_route.id)
    assert route is None

def test_get_verified_route_subscribers(sync_db_session: SyncSession, sample_route_request: RouteMonitorRequest):
    """Test retrieving verified subscribers for a route using a sync session."""
    # Create users
    user1 = User(email="verified@test.com", hashed_password="...", is_verified=True)
    user2 = User(email="unverified@test.com", hashed_password="...", is_verified=False)
    sync_db_session.add_all([user1, user2])
    sync_db_session.commit()

    # Create route
    route_data = sample_route_request.model_dump()
    route = MonitoredRoute(**route_data)
    sync_db_session.add(route)
    sync_db_session.commit()

    # Create subscriptions
    sub1 = UserRouteSubscription(user_id=user1.id, route_id=route.id)
    sub2 = UserRouteSubscription(user_id=user2.id, route_id=route.id)
    sync_db_session.add_all([sub1, sub2])
    sync_db_session.commit()

    subscribers = crud_route.get_verified_route_subscribers(db=sync_db_session, route_id=route.id)
    assert len(subscribers) == 1
    assert subscribers[0].email == "verified@test.com"

def test_deactivate_route_sync(sync_db_session: SyncSession, sample_route_request: RouteMonitorRequest):
    """Test deactivating a route synchronously."""
    route_data = sample_route_request.model_dump()
    route = MonitoredRoute(**route_data)
    sync_db_session.add(route)
    sync_db_session.commit()

    deactivated_route = crud_route.deactivate_route_sync(db=sync_db_session, route_id=route.id)
    assert deactivated_route.status == RouteStatusEnum.FOUND

def test_expire_route_sync(sync_db_session: SyncSession, sample_route_request: RouteMonitorRequest):
    """Test expiring a route synchronously."""
    route_data = sample_route_request.model_dump()
    route = MonitoredRoute(**route_data)
    sync_db_session.add(route)
    sync_db_session.commit()

    expired_route = crud_route.expire_route_sync(db=sync_db_session, route_id=route.id)
    assert expired_route.status == RouteStatusEnum.EXPIRED
