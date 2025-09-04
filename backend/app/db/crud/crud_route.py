from typing import List, Optional
import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session as SyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete, func 

from app.db.models.route import MonitoredRoute, UserRouteSubscription, RouteStatusEnum
from app.schemas.route import RouteMonitorRequest
from app.db.models.user import User

# --- Internal function to create route, assumes it doesn't exist ---
async def _create_monitored_route_internal(db: AsyncSession, *, route_data: dict) -> MonitoredRoute:
    """
    Internal helper to create a new monitored route record.
    Expects route_data dictionary with all necessary fields including datetimes.
    """
    # Ensure only valid columns for MonitoredRoute are passed
    valid_columns = {col.name for col in MonitoredRoute.__table__.columns}
    filtered_data = {k: v for k, v in route_data.items() if k in valid_columns}

    db_route = MonitoredRoute(**filtered_data)
    db.add(db_route)
    await db.commit()
    await db.refresh(db_route)
    return db_route

# --- Get or Create Logic ---
async def get_or_create_monitored_route(db: AsyncSession, *, route_in: RouteMonitorRequest) -> MonitoredRoute:
    """
    Gets an existing monitored route based on the composite key (regiojet_route_id, from_location_id, to_location_id)
    or creates a new one. Ensures the route is marked as active if found but inactive.
    """
    # Query based on the composite key
    stmt = select(MonitoredRoute).where(
        MonitoredRoute.regiojet_route_id == route_in.regiojet_route_id,
        MonitoredRoute.from_location_id == route_in.from_location_id,
        MonitoredRoute.to_location_id == route_in.to_location_id
    )
    result = await db.execute(stmt)
    existing_route = result.scalar_one_or_none()

    if existing_route:
        # If route exists but was deactivated (e.g., tickets found previously), reactivate it
        if existing_route.status != RouteStatusEnum.MONITORING:
            existing_route.status = RouteStatusEnum.MONITORING
            db.add(existing_route)
            await db.commit()
            await db.refresh(existing_route)
        return existing_route
    else:
        # Create new route if it doesn't exist
        # Prepare data dict from the input schema
        route_data = route_in.model_dump() # Use model_dump for Pydantic v2
        return await _create_monitored_route_internal(db=db, route_data=route_data)


async def create_user_subscription(db: AsyncSession, *, user_id: int, route_id: int) -> UserRouteSubscription:
    """
    Creates a link between a user and a monitored route.
    Handles potential race conditions or existing subscriptions gracefully.
    """
    # Check if subscription already exists
    stmt = select(UserRouteSubscription).where(
        UserRouteSubscription.user_id == user_id,
        UserRouteSubscription.route_id == route_id
    )
    result = await db.execute(stmt)
    existing_subscription = result.scalar_one_or_none()

    if existing_subscription:
        return existing_subscription # Already subscribed, just return it

    # If not existing, create it
    db_subscription = UserRouteSubscription(user_id=user_id, route_id=route_id)
    db.add(db_subscription)
    try:
        await db.commit()
        await db.refresh(db_subscription)
        return db_subscription
    except Exception as e:
        # Handle potential race condition if another request created it just now
        await db.rollback()
        # Attempt to fetch again after rollback
        result = await db.execute(stmt)
        existing_subscription_after_rollback = result.scalar_one_or_none()
        if existing_subscription_after_rollback:
            return existing_subscription_after_rollback
        else:
            # If it still doesn't exist after rollback, re-raise the original error
            print(f"Error creating subscription after rollback: {e}") # Log error
            raise e


async def get_user_subscriptions(db: AsyncSession, *, user_id: int) -> List[UserRouteSubscription]:
    """
    Retrieves all route subscriptions for a given user, including the related route details.
    """
    stmt = (
        select(UserRouteSubscription)
        .where(UserRouteSubscription.user_id == user_id)
        .options(selectinload(UserRouteSubscription.route)) # Eager load route details
        .order_by(UserRouteSubscription.created_at.desc()) # Optional: order by creation time
    )
    result = await db.execute(stmt)
    subscriptions = result.scalars().all()
    return list(subscriptions)


# --- Functions for Deleting Subscriptions/Routes ---

async def delete_user_subscription(db: AsyncSession, *, user_id: int, route_id: int) -> bool:
    """
    Deletes a specific user subscription for a monitored route.
    Returns True if a subscription was deleted, False otherwise.
    """
    stmt = (
        delete(UserRouteSubscription)
        .where(UserRouteSubscription.user_id == user_id)
         .where(UserRouteSubscription.route_id == route_id)
    )

    result = await db.execute(stmt)
    await db.commit() # Add commit back here
    return result.rowcount > 0

async def count_subscriptions_for_route(db: AsyncSession, *, route_id: int) -> int:
    """
    Counts the number of active subscriptions for a specific monitored route.
    """
    stmt = (
        select(func.count(UserRouteSubscription.user_id))
        .where(UserRouteSubscription.route_id == route_id)
    )
    result = await db.execute(stmt)
    count = result.scalar_one_or_none()
    return count if count is not None else 0

async def delete_monitored_route(db: AsyncSession, *, route_id: int) -> bool:
    """
    Deletes a monitored route record by its primary key (id).
    Returns True if the route was deleted, False otherwise.
    """
    stmt = (
        delete(MonitoredRoute)
         .where(MonitoredRoute.id == route_id)
    )

    result = await db.execute(stmt)
    await db.commit() # Add commit back here
    # result.rowcount gives the number of deleted rows
    return result.rowcount > 0


def get_verified_route_subscribers(db: SyncSession, *, route_id: int) -> List[User]:
    """
    Retrieves all verified users subscribed to a specific route.
    (Synchronous version for Celery tasks)
    """
    stmt = (
        select(User)
        .join(User.subscriptions) # Assuming User.subscriptions links to UserRouteSubscription
        .where(
            UserRouteSubscription.route_id == route_id,
            User.is_verified == True # Ensure user is verified
        )
    )
    result = db.execute(stmt)
    users = result.scalars().all()
    return list(users)

def deactivate_route_sync(db: SyncSession, *, route_id: int) -> Optional[MonitoredRoute]:
     """
     Deactivates a route (sets status=FOUND)
     (Synchronous version for Celery tasks - used when tickets are found)
     """
     stmt = select(MonitoredRoute).where(MonitoredRoute.id == route_id)
     result = db.execute(stmt)
     route = result.scalar_one_or_none()

     if route and route.status == RouteStatusEnum.MONITORING:
         route.status = RouteStatusEnum.FOUND
         db.add(route)
         try:
             db.commit()
             db.refresh(route)
             return route
         except Exception as e:
             db.rollback()
             print(f"Error deactivating route {route_id}: {e}") # Log error
             # Decide how to handle commit errors, maybe raise?
             raise e
     elif route:
         # Route already inactive, return it as is
         return route
     else:
         # Route not found
         return None


def expire_route_sync(db: SyncSession, *, route_id: int) -> Optional[MonitoredRoute]:
     """
     Deactivates a route (status = EXPIRED) because its departure time has passed.
     (Synchronous version for Celery tasks)
     """
     stmt = select(MonitoredRoute).where(MonitoredRoute.id == route_id)
     result = db.execute(stmt)
     route = result.scalar_one_or_none()

     if route:
         route.status = RouteStatusEnum.EXPIRED
         db.add(route)
         try:
             db.commit()
             db.refresh(route)
             return route
         except Exception as e:
             db.rollback()
             print(f"Error expiring route {route_id}: {e}") # Log error
             raise e
     elif route:
         # Route already inactive, return it as is
         return route
     else:
         # Route not found
         return None


async def get_monitored_route_by_id(db: AsyncSession, *, route_id: int) -> Optional[MonitoredRoute]:
    """Retrieves a single monitored route by its primary key (id)."""
    stmt = select(MonitoredRoute).where(MonitoredRoute.id == route_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_subscription_for_route(db: AsyncSession, *, user_id: int, route_id: int) -> Optional[UserRouteSubscription]:
    """Retrieves a specific user subscription for a route, if it exists."""
    stmt = select(UserRouteSubscription).where(
        UserRouteSubscription.user_id == user_id,
        UserRouteSubscription.route_id == route_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def update_route_status_and_last_checked(
    db: AsyncSession, *, route: MonitoredRoute, new_status: RouteStatusEnum, last_checked_at: datetime.datetime
) -> MonitoredRoute:
    """Updates the status and last_checked_at timestamp of a monitored route."""
    route.status = new_status
    route.last_checked_at = last_checked_at
    db.add(route)
    await db.commit()
    await db.refresh(route)
    return route
