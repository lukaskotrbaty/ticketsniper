import datetime
import json
import logging
from typing import List, Optional, Dict, Any

import redis.asyncio as redis_async # Alias async redis
import redis # Import sync redis
from fastapi import HTTPException, status

from app.core.config import settings
from app.schemas.location import Location
from app.schemas.available_route import AvailableRoute
from app.services.regiojet_api_client import _fetch_regiojet_api
from app.services.regiojet_data_parser import _parse_locations_response, _parse_single_route, ParsingError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
LOCATION_CACHE_KEY = "regiojet_locations"
LOCATION_CACHE_TTL_SECONDS = settings.LOCATION_CACHE_TTL_SECONDS

# --- Async Caching Helpers ---

async def _get_locations_from_cache(redis_client: redis_async.Redis) -> Optional[List[Location]]:
    """ Attempts to retrieve and validate locations from async cache with detailed error logging. """
    try:
        cached_locations = await redis_client.get(LOCATION_CACHE_KEY)
        if cached_locations:
            logger.debug("Async Cache hit for locations")
            try:
                locations_data = json.loads(cached_locations)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding cached locations: {e}. Cache invalid.")
                return None # Stop if JSON is invalid

            if isinstance(locations_data, list):
                validated_locations = []
                validation_failed = False
                for i, loc_data in enumerate(locations_data): # Iterate and validate one by one
                    try:
                        validated_locations.append(Location.model_validate(loc_data))
                    except Exception as e:
                        # Log the specific error and the problematic data item
                        logger.warning(f"Cached location data validation failed at index {i} for data {loc_data}: {e}. Cache invalid.")
                        validation_failed = True
                        break # Stop validation on first error
                if not validation_failed:
                    logger.debug(f"Successfully validated {len(validated_locations)} locations from async cache.")
                    return validated_locations # Return list only if all items validated
            else:
                 logger.warning("Invalid location data format in async cache (expected list). Cache invalid.")
    except redis_async.RedisError as e:
        logger.error(f"Async Redis error getting locations cache: {e}.")
    # Return None if cache miss, JSON error, format error, validation error, or Redis error
    return None

async def _set_locations_to_cache(redis_client: redis_async.Redis, locations: List[Location]):
    """ Sets validated locations into async cache. """
    try:
        # Convert Pydantic models back to dicts for JSON serialization
        locations_to_cache = [loc.model_dump() for loc in locations]
        await redis_client.set(
            LOCATION_CACHE_KEY,
            json.dumps(locations_to_cache),
            ex=LOCATION_CACHE_TTL_SECONDS
        )
        logger.info(f"Successfully cached {len(locations)} locations to async cache.")
    except redis_async.RedisError as e:
        logger.error(f"Async Redis error setting locations cache: {e}")
    except Exception as e:
         logger.error(f"Failed to serialize locations for async caching: {e}")


# --- Sync Caching Helper (for Celery) ---

def _get_locations_from_cache_sync() -> Optional[List[Location]]:
    """ Attempts to retrieve and validate locations from sync cache with detailed error logging. """
    redis_client: redis.Redis | None = None
    try:
        # Create a sync client instance - consider pooling for frequent calls
        redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        cached_locations = redis_client.get(LOCATION_CACHE_KEY)
        if cached_locations:
            logger.debug("Sync Cache hit for locations")
            try:
                locations_data = json.loads(cached_locations)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding sync cached locations: {e}. Cache invalid.")
                return None

            if isinstance(locations_data, list):
                validated_locations = []
                validation_failed = False
                for i, loc_data in enumerate(locations_data):
                    try:
                        validated_locations.append(Location.model_validate(loc_data))
                    except Exception as e:
                        logger.warning(f"Sync cached location data validation failed at index {i} for data {loc_data}: {e}. Cache invalid.")
                        validation_failed = True
                        break
                if not validation_failed:
                    logger.debug(f"Successfully validated {len(validated_locations)} locations from sync cache.")
                    return validated_locations
            else:
                 logger.warning("Invalid location data format in sync cache (expected list). Cache invalid.")
    except redis.RedisError as e:
        logger.error(f"Sync Redis error getting locations cache: {e}.")
    except Exception as e:
        # Catch other potential errors like connection issues during client creation
        logger.exception(f"Unexpected error getting sync locations cache: {e}")
    finally:
        if redis_client:
            try:
                redis_client.close()
            except Exception as e:
                logger.error(f"Error closing sync redis client: {e}")
    # Return None if cache miss, JSON error, format error, validation error, or Redis error
    return None


# --- Service Functions ---

async def get_locations(redis_client: redis_async.Redis) -> List[Location]:
    """
    Fetches the list of Regiojet locations (cities and stations).
    Uses cache and falls back to API fetch, parsing, validation, and caching.
    """
    # 1. Try cache
    cached_data = await _get_locations_from_cache(redis_client)
    if cached_data is not None:
        return cached_data

    # 2. Fetch from API if cache miss/error
    logger.info("Cache miss or error for locations. Fetching from Regiojet API.")
    try:
        api_data = await _fetch_regiojet_api(
            endpoint="/consts/locations",
            headers={"X-Lang": "cs"},
            timeout=10.0
        )
    except HTTPException:
        raise # Re-raise exceptions from the client helper
    except Exception as e: # Catch unexpected errors during fetch call itself
        logger.exception(f"Unexpected error calling _fetch_regiojet_api for locations: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch location data.")

    # 3. Parse API response
    try:
        parsed_locations_dicts = _parse_locations_response(api_data)
    except ParsingError as e:
        # Handle critical parsing error (e.g., wrong top-level structure)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error parsing locations response: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to parse location data.")

    # 4. Validate with Pydantic schema
    try:
         locations = [Location.model_validate(loc) for loc in parsed_locations_dicts]
    except Exception as e:
         logger.error(f"Pydantic validation failed for parsed locations: {e}")
         raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail="Failed to validate location data from Regiojet API."
         )

    # 5. Cache the result
    await _set_locations_to_cache(redis_client, locations)

    return locations


async def get_available_routes(
    from_location_id: str,
    to_location_id: str,
    from_location_type: str,
    to_location_type: str,
    departure_date: datetime.date
) -> List[AvailableRoute]:
    """
    Fetches and parses available routes for a given origin, destination, and date.
    """
    # 1. Prepare params and headers
    params = {
        "departureDate": departure_date.isoformat(),
        "fromLocationId": from_location_id,
        "toLocationId": to_location_id,
        "fromLocationType": from_location_type,
        "toLocationType": to_location_type,
        "tariffs": "REGULAR"
    }
    headers = {"X-Lang": "cs", "X-Currency": "CZK"}

    # 2. Fetch from API
    try:
        api_data = await _fetch_regiojet_api(
            endpoint="/routes/search/simple",
            params=params,
            headers=headers
        )
    except HTTPException:
        raise # Re-raise exceptions from the client helper
    except Exception as e:
        logger.exception(f"Unexpected error calling _fetch_regiojet_api for routes: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch available routes data.")

    # 3. Parse API response
    available_routes_dicts: List[Dict[str, Any]] = []
    if isinstance(api_data, dict) and isinstance(api_data.get("routes"), list):
        routes_list = api_data["routes"]
        for route_data in routes_list:
            parsed_route = _parse_single_route(route_data, departure_date)
            if parsed_route:
                available_routes_dicts.append(parsed_route)
    else:
        logger.warning(f"Unexpected API response format for available routes: {type(api_data)}. Expected dict with 'routes' list.")
        # Return empty list if format is wrong, as parsing cannot proceed

    # 4. Validate with Pydantic schema
    try:
        validated_routes = [AvailableRoute.model_validate(route_dict) for route_dict in available_routes_dicts]
        logger.info(f"Found and validated {len(validated_routes)} available routes for {departure_date}.")
        return validated_routes
    except Exception as e:
        logger.error(f"Pydantic validation failed for parsed routes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate available routes data from Regiojet API."
        )
