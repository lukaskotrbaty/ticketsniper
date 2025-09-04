from typing import List, Optional
import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, status

# Use relative imports for intra-app modules
from app.api import deps
from app.schemas.location import Location
from app.services import regiojet_data_service

router = APIRouter()

@router.get("/locations", response_model=List[Location])
async def read_locations(
    query: Optional[str] = None,
    redis_client: redis.Redis = Depends(deps.get_redis_client) # Assuming get_redis_client exists in deps
) -> List[Location]:
    """
    Retrieves a list of Regiojet locations (cities and stations).
    Optionally filters the list based on a query string (case-insensitive substring match on name).
    """
    try:
        locations = await regiojet_data_service.get_locations(redis_client=redis_client)
    except HTTPException as e:
        # Re-raise HTTP exceptions from the service layer
        raise e
    except Exception as e:
        # Catch-all for unexpected errors during location fetching
        # Log the error e
        print(f"Unexpected error in /locations endpoint: {e}") # Basic logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Při načítání lokací došlo k chybě."
        )

    if query:
        query_lower = query.lower()
        filtered_locations = [
            loc for loc in locations if query_lower in loc.name.lower()
        ]
        return filtered_locations
    else:
        return locations
