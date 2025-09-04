import httpx
import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, status

# Import settings
from app.core.config import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use base URL from settings
REGIOJET_API_BASE_URL = settings.REGIOJET_API_BASE_URL

async def _fetch_regiojet_api(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 15.0 # Default timeout
) -> Any:
    """
    Helper function to fetch data from a Regiojet API endpoint.

    Handles common HTTP errors and raises appropriate FastAPI HTTPExceptions.
    """
    api_url = f"{REGIOJET_API_BASE_URL}{endpoint}"
    # Consider adding a default User-Agent header if needed
    request_headers = headers or {}

    logger.info(f"Fetching from Regiojet API: {api_url} with params: {params}, headers: {request_headers}")

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(api_url, params=params, headers=request_headers)
            response.raise_for_status() # Raise HTTPStatusError for 4xx/5xx responses
            return response.json()

    except httpx.TimeoutException:
        logger.error(f"Timeout fetching from {api_url}")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=f"Regiojet API timed out ({endpoint}).")
    except httpx.RequestError as e:
        logger.error(f"Request error fetching from {api_url}: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Could not connect to Regiojet API ({endpoint}).")
    except httpx.HTTPStatusError as e:
        logger.error(f"Regiojet API error fetching from {api_url}: {e.response.status_code} - {e.response.text}")
        # Handle specific client errors if needed
        if e.response.status_code == 400:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid parameters for Regiojet API ({endpoint}): {e.response.text}")
        # Treat other 4xx/5xx errors as Bad Gateway
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Received an error from Regiojet API ({endpoint}).")
    except Exception as e:
        logger.exception(f"Unexpected error fetching from {api_url}: {e}") # Log full traceback
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred while contacting Regiojet API ({endpoint}).")


# --- Synchronous Version ---

def _fetch_regiojet_api_sync(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 15.0 # Default timeout
) -> Any:
    """
    Synchronous helper function to fetch data from a Regiojet API endpoint.

    Handles common HTTP errors and raises appropriate FastAPI HTTPExceptions.
    """
    api_url = f"{REGIOJET_API_BASE_URL}{endpoint}"
    request_headers = headers or {}

    logger.info(f"Fetching SYNC from Regiojet API: {api_url} with params: {params}, headers: {request_headers}")

    try:
        # Use synchronous client
        with httpx.Client(timeout=timeout) as client:
            response = client.get(api_url, params=params, headers=request_headers)
            response.raise_for_status() # Raise HTTPStatusError for 4xx/5xx responses
            return response.json()

    except httpx.TimeoutException:
        logger.error(f"Timeout fetching SYNC from {api_url}")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=f"Regiojet API timed out ({endpoint}).")
    except httpx.RequestError as e:
        logger.error(f"Request error fetching SYNC from {api_url}: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Could not connect to Regiojet API ({endpoint}).")
    except httpx.HTTPStatusError as e:
        logger.error(f"Regiojet API error fetching SYNC from {api_url}: {e.response.status_code} - {e.response.text}")
        if e.response.status_code == 400:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid parameters for Regiojet API ({endpoint}): {e.response.text}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Received an error from Regiojet API ({endpoint}).")
    except Exception as e:
        logger.exception(f"Unexpected error fetching SYNC from {api_url}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred while contacting Regiojet API ({endpoint}).")
