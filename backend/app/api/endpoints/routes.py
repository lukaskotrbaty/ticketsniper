import datetime
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.models import UserRouteSubscription
from app.db.models.user import User
from app.db.models.route import RouteStatusEnum
from app.schemas.route import RouteMonitorRequest, MonitoredRouteInfo, RouteMonitorResponse, RouteRestartResponse
from app.schemas.available_route import AvailableRoute
from app.db.crud import crud_route
from app.services import regiojet_data_service
# Import the ASYNC checker service function
from app.services.regiojet_checker_service import check_route_availability

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/available", response_model=List[AvailableRoute])
async def get_available_routes_endpoint(
    from_location_id: str = Query(..., description="Origin location ID (Regiojet)"),
    to_location_id: str = Query(..., description="Destination location ID (Regiojet)"),
    from_location_type: str = Query(..., description="Origin location type ('CITY' or 'STATION')"),
    to_location_type: str = Query(..., description="Destination location type ('CITY' or 'STATION')"),
    departure_date: datetime.date = Query(..., description="Date of departure (YYYY-MM-DD)"),
    current_user: User = Depends(deps.get_current_active_user) # Requires authentication
) -> List[AvailableRoute]:
    """
    Retrieves a list of available Regiojet routes for the specified criteria.
    """
    try:
        available_routes = await regiojet_data_service.get_available_routes(
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            from_location_type=from_location_type,
            to_location_type=to_location_type,
            departure_date=departure_date
        )
        return available_routes
    except HTTPException as e:
        # Re-raise HTTP exceptions from the service layer
        raise e
    except Exception as e:
        # Catch-all for unexpected errors
        print(f"Unexpected error in /routes/available endpoint: {e}") # Basic logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Při načítání dostupných spojů došlo k chybě."
        )


@router.post("/monitor", response_model=RouteMonitorResponse)
async def create_monitoring_request(
    *,
    response: Response,
    db: AsyncSession = Depends(deps.get_db),
    route_in: RouteMonitorRequest,
    current_user: User = Depends(deps.get_current_active_user)
) -> RouteMonitorResponse:
    """
    Endpoint for users to submit a new route monitoring request.
    Performs an initial availability check using RegiojetCheckerService.
    If tickets are available, returns 200 OK with details.
    If tickets are unavailable, saves the monitoring request and returns 201 Created.
    """
    # 1. Perform initial availability check
    # Create a temporary MonitoredRoute instance from input data for the checker
    # Note: We only strictly need fields used by check_route_availability
    temp_route_data = {
        "regiojet_route_id": route_in.regiojet_route_id,
        "from_location_id": route_in.from_location_id,
        "from_location_type": route_in.from_location_type,
        "to_location_id": route_in.to_location_id,
        "to_location_type": route_in.to_location_type,
        "departure_datetime": route_in.departure_datetime,
        "arrival_datetime": route_in.arrival_datetime,
    }
    # temp_route = MonitoredRoute(**temp_route_data) # This would try to create a DB model instance
    # For check_route_availability, we pass the dictionary-like object or a Pydantic model if the service expects it.
    # Assuming check_route_availability can handle a dictionary or an object with these attributes:
    class TempRouteForCheck:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    temp_route = TempRouteForCheck(**temp_route_data)

    try:
        is_available, details = await check_route_availability(route=temp_route)
    except HTTPException as e:
        # If async checker service raises HTTPException, re-raise it
        logger.error(f"Error during initial check for route {route_in.regiojet_route_id}: {e.detail}")
        raise e
    except Exception as e:
        # Catch unexpected errors from the checker
        logger.exception(f"Unexpected error during initial check for route {route_in.regiojet_route_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Během úvodní kontroly dostupnosti došlo k neočekávané chybě."
        )

    # 2. Handle based on availability
    if is_available:
        # Tickets are available, do not save monitoring, return 200 OK
        response.status_code = status.HTTP_200_OK
        return RouteMonitorResponse(
            message="Jízdenky jsou pro tuto trasu aktuálně dostupné. Sledování nebylo spuštěno.",
            available=True,
            details=details
        )
    else:
        # Tickets are not available, proceed to save monitoring request
        # 3. Get or create the MonitoredRoute using regiojet_route_id
        try:
            db_route = await crud_route.get_or_create_monitored_route(db=db, route_in=route_in)
        except ValueError as e: # Should not happen if Pydantic validation passed, but good practice
             logger.error(f"Validation error creating route {route_in.regiojet_route_id}: {e}")
             raise HTTPException(
                 status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                 detail=str(e),
             )
        except Exception as e:
            logger.exception(f"Error getting or creating monitored route {route_in.regiojet_route_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Nepodařilo se uložit nebo načíst informace o trase.",
            )

        # 4. Create the UserRouteSubscription link (handles existing subscriptions)
        try:
            await crud_route.create_user_subscription(db=db, user_id=current_user.id, route_id=db_route.id)
        except Exception as e:
            logger.exception(f"Error creating subscription for user {current_user.id} and route {db_route.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Nepodařilo se přihlásit uživatele ke sledování trasy.",
            )

        # Monitoring saved successfully, return 201 Created
        response.status_code = status.HTTP_201_CREATED
        return RouteMonitorResponse(
            message="Sledování bylo úspěšně spuštěno.",
            available=False,
            details=None # No details needed when monitoring starts
        )


@router.get("/monitored", response_model=List[MonitoredRouteInfo])
async def get_monitored_routes(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    redis_client = Depends(deps.get_redis_client) # Add Redis client dependency
) -> List[MonitoredRouteInfo]:
    """
    Retrieves the list of routes monitored by the current user, including location names.
    """
    subscriptions: List[UserRouteSubscription] = await crud_route.get_user_subscriptions(db=db, user_id=current_user.id)

    # Fetch location names (ideally from cache)
    location_map = {}
    try:
        # Use the existing get_locations function which utilizes caching
        all_locations = await regiojet_data_service.get_locations(redis_client) # Pass redis client
        # Create a map of ID to name (using only the 'name' attribute)
        location_map = {loc.id: loc.name for loc in all_locations}
    except Exception as e:
        logger.warning(f"Could not fetch/process location names for /monitored endpoint: {e}", exc_info=True)
        # Proceed without names if fetching fails, log the warning

    # Map the subscription and related route data to the response schema
    results: List[MonitoredRouteInfo] = []
    for sub in subscriptions:
        if sub.route: # Ensure the relationship loaded correctly
            route_data = sub.route
            results.append(
                MonitoredRouteInfo(
                    id=route_data.id, 
                    route_id=route_data.regiojet_route_id,
                    from_location_id=route_data.from_location_id,
                    from_location_type=route_data.from_location_type,
                    to_location_id=route_data.to_location_id,
                    to_location_type=route_data.to_location_type,
                    from_location_name=location_map.get(route_data.from_location_id),
                    to_location_name=location_map.get(route_data.to_location_id),
                    departure_datetime=route_data.departure_datetime,
                    arrival_datetime=route_data.arrival_datetime,
                    status=str(route_data.status.value if hasattr(route_data.status, 'value') else route_data.status),
                    created_at=sub.created_at
                )
            )
    return results


@router.delete("/monitor/{db_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_monitoring_request(
    *,
    db_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Cancels the monitoring subscription for the current user and the specified route ID.
    If this was the last user monitoring this route, the route itself is deleted.
    """
    try:
        deleted = await crud_route.delete_user_subscription(
            db=db, user_id=current_user.id, route_id=db_id
        )

        if not deleted:
            # If no subscription was deleted for this user/route, raise 404
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sledování pro tohoto uživatele a trasu nebylo nalezeno.",
            )

        # Check if any other users are still monitoring this route
        remaining_subscriptions = await crud_route.count_subscriptions_for_route(
            db=db, route_id=db_id
        )

        if remaining_subscriptions == 0:
            # If no one else is monitoring, delete the route itself
            await crud_route.delete_monitored_route(db=db, route_id=db_id)
            logger.info(f"Deleted monitored route with id {db_id} as it had no more subscribers.")

        # Transaction should be committed automatically by the dependency if no exceptions
        logger.info(f"User {current_user.id} successfully cancelled subscription for route {db_id}.")
        # Return 204 No Content implicitly by FastAPI if no content is returned

    except HTTPException as e:
        # Re-raise HTTP exceptions (like the 404)
        # Consider adding rollback here if the dependency doesn't handle it on HTTPExceptions
        # await db.rollback() # <-- Potentially needed depending on deps.get_db implementation
        raise e
    except Exception as e:
        # Catch potential DB errors during the operations
        logger.exception(f"Error cancelling subscription for user {current_user.id}, route {db_id}: {e}")
        # Rollback should happen automatically if the dependency is set up correctly
        # await db.rollback() # <-- Potentially needed depending on deps.get_db implementation


@router.post("/monitored-routes/{route_db_id}/restart", response_model=RouteRestartResponse)
async def restart_monitoring_request(
    *,
    route_db_id: int,
    response: Response,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> RouteRestartResponse:
    """
    Restarts monitoring for a specific route that was previously found.
    """
    # 1. Fetch the MonitoredRoute by its database ID
    db_route = await crud_route.get_monitored_route_by_id(db=db, route_id=route_db_id)
    if not db_route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sledovaná trasa nebyla nalezena.")

    # 2. Verify the user is subscribed to this route
    subscription = await crud_route.get_user_subscription_for_route(db=db, user_id=current_user.id, route_id=db_route.id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nemáte oprávnění restartovat sledování této trasy.")

    # 3. Check if the route status is FOUND
    if db_route.status != RouteStatusEnum.FOUND:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Sledování této trasy nelze restartovat, protože její aktuální stav je '{db_route.status.value}' (očekáváno 'FOUND')."
        )

    # 4. Perform availability check (using the existing db_route object)
    try:
        is_available, availability_details = await check_route_availability(route=db_route)
    except HTTPException as e:
        logger.error(f"Error during availability check for restarting route {db_route.id}: {e.detail}")
        raise e # Re-raise HTTPException from checker service
    except Exception as e:
        logger.exception(f"Unexpected error during availability check for restarting route {db_route.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Během kontroly dostupnosti při restartu došlo k neočekávané chybě."
        )

    # 5. Handle based on availability
    if is_available:
        # Tickets are still available, do not change status, return 200 OK
        response.status_code = status.HTTP_200_OK
        return RouteRestartResponse(
            message="Jízdenky jsou pro tuto trasu stále dostupné. Sledování nebylo znovu aktivováno.",
            restarted=False,
            details=availability_details
        )
    else:
        # Tickets are not available, update route status to MONITORING
        try:
            await crud_route.update_route_status_and_last_checked(
                db=db,
                route=db_route,
                new_status=RouteStatusEnum.MONITORING,
                last_checked_at=datetime.datetime.now(datetime.timezone.utc)
            )
        except Exception as e:
            logger.exception(f"Error updating route {db_route.id} to MONITORING during restart: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Nepodařilo se aktualizovat stav sledované trasy."
            )

        response.status_code = status.HTTP_200_OK
        return RouteRestartResponse(
            message="Sledování trasy bylo úspěšně obnoveno.",
            restarted=True,
            details=None
        )
