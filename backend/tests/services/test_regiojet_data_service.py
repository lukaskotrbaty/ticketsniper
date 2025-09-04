import pytest
import datetime
from unittest.mock import patch, AsyncMock

from fastapi import HTTPException, status
from app.services import regiojet_data_service
from app.services.regiojet_data_parser import ParsingError
from app.schemas.location import Location
from app.schemas.available_route import AvailableRoute

# Mock data returned by the PARSER
MOCK_PARSED_LOCATIONS = [
    {"id": "1", "name": "City A", "type": "CITY", "normalized_name": "city a"},
    {"id": "2", "name": "Station B", "type": "STATION", "normalized_name": "station b"},
]

MOCK_PARSED_ROUTES = [
    {
        "routeId": "123", "departureTime": datetime.datetime(2025, 1, 1, 10, 0),
        "arrivalTime": datetime.datetime(2025, 1, 1, 12, 0), "freeSeatsCount": 5,
        "vehicleTypes": ["TRAIN"], "fromStationId": "1", "toStationId": "2"
    }
]

@pytest.mark.asyncio
@patch("app.services.regiojet_data_service._get_locations_from_cache", new_callable=AsyncMock)
async def test_get_locations_cache_hit(mock_get_from_cache):
    """Test get_locations returns data from cache successfully."""
    # Arrange
    mock_redis_client = AsyncMock()
    # The cache function is expected to return validated Pydantic models
    mock_get_from_cache.return_value = [Location.model_validate(loc) for loc in MOCK_PARSED_LOCATIONS]

    # Act
    locations = await regiojet_data_service.get_locations(redis_client=mock_redis_client)

    # Assert
    assert len(locations) == 2
    assert locations[0].name == "City A"
    mock_get_from_cache.assert_awaited_once_with(mock_redis_client)

@pytest.mark.asyncio
@patch("app.services.regiojet_data_service._set_locations_to_cache", new_callable=AsyncMock)
@patch("app.services.regiojet_data_service._parse_locations_response")
@patch("app.services.regiojet_data_service._fetch_regiojet_api", new_callable=AsyncMock)
@patch("app.services.regiojet_data_service._get_locations_from_cache", new_callable=AsyncMock)
async def test_get_locations_cache_miss(mock_get_cache, mock_fetch, mock_parse, mock_set_cache):
    """Test cache miss, successful fetch, parse, validate, cache, and return."""
    # Arrange
    mock_redis_client = AsyncMock()
    mock_get_cache.return_value = None  # Cache miss
    mock_fetch.return_value = {"raw_api_data": "..."}
    mock_parse.return_value = MOCK_PARSED_LOCATIONS

    # Act
    locations = await regiojet_data_service.get_locations(redis_client=mock_redis_client)

    # Assert
    assert len(locations) == 2
    assert locations[1].name == "Station B"
    mock_fetch.assert_awaited_once()
    mock_parse.assert_called_once_with({"raw_api_data": "..."})
    mock_set_cache.assert_awaited_once()

@pytest.mark.asyncio
@patch("app.services.regiojet_data_service._get_locations_from_cache", new_callable=AsyncMock)
async def test_get_locations_fetch_error(mock_get_cache):
    """Test handling HTTPException raised by the API client during fetch."""
    # Arrange
    mock_redis_client = AsyncMock()
    mock_get_cache.return_value = None # Cache miss
    # Patch the fetch function within the test to control its side effect
    with patch("app.services.regiojet_data_service._fetch_regiojet_api", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await regiojet_data_service.get_locations(redis_client=mock_redis_client)
        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

@pytest.mark.asyncio
@patch("app.services.regiojet_data_service._parse_single_route")
@patch("app.services.regiojet_data_service._fetch_regiojet_api", new_callable=AsyncMock)
async def test_get_available_routes_success(mock_fetch, mock_parse):
    """Test successful fetching, parsing, and validation of available routes."""
    # Arrange
    mock_fetch.return_value = {"routes": [{"id": 1}, {"id": 2}]}
    # Let the parser return one valid route and one None
    mock_parse.side_effect = [MOCK_PARSED_ROUTES[0], None]
    test_date = datetime.date(2025, 1, 1)

    # Act
    routes = await regiojet_data_service.get_available_routes("1", "2", "CITY", "CITY", test_date)

    # Assert
    assert len(routes) == 1
    assert isinstance(routes[0], AvailableRoute)
    assert routes[0].routeId == "123"
    mock_fetch.assert_awaited_once()
    assert mock_parse.call_count == 2

@pytest.mark.asyncio
@patch("app.services.regiojet_data_service._fetch_regiojet_api", new_callable=AsyncMock)
async def test_get_available_routes_fetch_error(mock_fetch):
    """Test handling HTTPException from API client for available routes."""
    # Arrange
    mock_fetch.side_effect = HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT)
    test_date = datetime.date(2025, 1, 1)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await regiojet_data_service.get_available_routes("1", "2", "CITY", "CITY", test_date)
    assert exc_info.value.status_code == status.HTTP_504_GATEWAY_TIMEOUT
