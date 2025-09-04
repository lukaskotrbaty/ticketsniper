import logging
from typing import Any, Dict, Optional, Tuple
import httpx # Keep for potential type hints if needed, though client is sync now
from urllib.parse import urlencode

# Import settings
from app.core.config import settings
from app.db.models.route import MonitoredRoute
# Import both sync and async helpers
from app.services.regiojet_api_client import _fetch_regiojet_api, _fetch_regiojet_api_sync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use booking base URL from settings
REGIOJET_BOOKING_BASE_URL = settings.REGIOJET_BOOKING_BASE_URL

# --- Synchronous Version (for Celery) ---
def check_route_availability_sync(
    route: MonitoredRoute
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Checks the availability of a specific Regiojet route instance using the API.

    Args:
        route: The MonitoredRoute database object containing route details.

    Returns:
        A tuple:
        - bool: True if tickets are available, False otherwise.
        - Optional[Dict[str, Any]]: A dictionary with details if available
          (freeSeatsCount, priceFrom, priceTo, booking_link), otherwise None.
    """
    if not route.regiojet_route_id:
        logger.error(f"Missing regiojet_route_id for route ID {route.id}")
        return False, None

    endpoint = f"/routes/{route.regiojet_route_id}/simple"
    params = {
        "fromStationId": route.from_location_id,
        "toStationId": route.to_location_id,
        # Add other necessary params if discovered later
    }
    headers = {
        "X-Lang": "cs",
        "X-Currency": "CZK"
        # Add User-Agent if needed
    }

    try:
        # Call the synchronous helper function
        api_response = _fetch_regiojet_api_sync(
            endpoint=endpoint, params=params, headers=headers
        )

        if not isinstance(api_response, dict):
            logger.error(f"Unexpected API response type for route {route.regiojet_route_id}: {type(api_response)}")
            return False, None

        free_seats = api_response.get("freeSeatsCount", 0)
        is_available = free_seats > 0

        if is_available:
            # Construct booking link
            booking_params = {
                "departureDate": route.departure_datetime.date().isoformat(),
                "fromLocationId": route.from_location_id,
                "toLocationId": route.to_location_id,
                "fromLocationType": route.from_location_type,
                "toLocationType": route.to_location_type,
            }
            booking_link = f"{REGIOJET_BOOKING_BASE_URL}?{urlencode(booking_params)}"

            details = {
                "freeSeatsCount": free_seats,
                "priceFrom": api_response.get("priceFrom"),
                "priceTo": api_response.get("priceTo"),
                "booking_link": booking_link,
                "arrivalTime": api_response.get("arrivalTime"),
            }
            logger.info(f"Tickets found for route {route.regiojet_route_id}: {free_seats} seats.")
            return True, details
        else:
            logger.info(f"No tickets found for route {route.regiojet_route_id}.")
            return False, None

    except httpx.HTTPStatusError as e:
        # Specific handling for 404 which might mean the route ID is invalid/expired
        if e.response.status_code == 404:
             logger.warning(f"Route {route.regiojet_route_id} not found on Regiojet API (404). Treating as unavailable.")
             return False, None
        # Re-raise other HTTP errors handled by _fetch_regiojet_api to be caught by endpoint/caller
        logger.error(f"HTTPStatusError checking route {route.regiojet_route_id}: {e}")
        raise # Re-raise the HTTPException raised by _fetch_regiojet_api
    except KeyError as e:
        logger.error(f"Missing expected key in API response for route {route.regiojet_route_id}: {e}")
        return False, None
    except Exception as e:
        # Catch any other unexpected errors during processing
        logger.exception(f"Unexpected error checking availability for route {route.regiojet_route_id}: {e}")
        # Depending on policy, might want to raise or return False
        return False, None

# --- Asynchronous Version (for FastAPI endpoint) ---
async def check_route_availability(
    route: MonitoredRoute,
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Asynchronously checks the availability of a specific Regiojet route instance.

    Args:
        route: The MonitoredRoute database object containing route details.

    Returns:
        A tuple:
        - bool: True if tickets are available, False otherwise.
        - Optional[Dict[str, Any]]: A dictionary with details if available
          (freeSeatsCount, priceFrom, priceTo, booking_link), otherwise None.
    """
    if not route.regiojet_route_id:
        logger.error(f"Missing regiojet_route_id for route ID {route.id}")
        return False, None

    endpoint = f"/routes/{route.regiojet_route_id}/simple"
    params = {
        "fromStationId": route.from_location_id,
        "toStationId": route.to_location_id,
    }
    headers = {
        "X-Lang": "cs",
        "X-Currency": "CZK"
    }

    try:
        # Call the asynchronous helper function
        api_response = await _fetch_regiojet_api(
            endpoint=endpoint, params=params, headers=headers
        )

        if not isinstance(api_response, dict):
            logger.error(f"Unexpected API response type for route {route.regiojet_route_id}: {type(api_response)}")
            return False, None

        free_seats = api_response.get("freeSeatsCount", 0)
        is_available = free_seats > 0

        if is_available:
            booking_params = {
                "departureDate": route.departure_datetime.date().isoformat(),
                "fromLocationId": route.from_location_id,
                "toLocationId": route.to_location_id,
                "fromLocationType": route.from_location_type,
                "toLocationType": route.to_location_type,
            }
            booking_link = f"{REGIOJET_BOOKING_BASE_URL}?{urlencode(booking_params)}"
            details = {
                "freeSeatsCount": free_seats,
                "priceFrom": api_response.get("priceFrom"),
                "priceTo": api_response.get("priceTo"),
                "booking_link": booking_link,
            }
            logger.info(f"Tickets found for route {route.regiojet_route_id}: {free_seats} seats.")
            return True, details
        else:
            logger.info(f"No tickets found for route {route.regiojet_route_id}.")
            return False, None

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
             logger.warning(f"Route {route.regiojet_route_id} not found on Regiojet API (404). Treating as unavailable.")
             return False, None
        logger.error(f"HTTPStatusError checking route {route.regiojet_route_id}: {e}")
        raise # Re-raise the HTTPException raised by _fetch_regiojet_api
    except KeyError as e:
        logger.error(f"Missing expected key in API response for route {route.regiojet_route_id}: {e}")
        return False, None
    except Exception as e:
        logger.exception(f"Unexpected error checking availability for route {route.regiojet_route_id}: {e}")
        return False, None
