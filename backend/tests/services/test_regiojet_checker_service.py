import pytest
from unittest.mock import patch, AsyncMock
from fastapi import HTTPException, status

from app.services import regiojet_checker_service
from app.schemas.route import Route

# A mock route object that would be passed to the service
MOCK_DB_ROUTE = Route(
    id=1,
    regiojet_route_id="12345",
    departure_datetime="2025-12-01T10:00:00+01:00",
    arrival_datetime="2025-12-01T12:00:00+01:00",
    from_location_id="100",
    from_location_type="STATION",
    to_location_id="200",
    to_location_type="STATION",
    status="MONITORING",
    last_checked_at=None,
    created_at="2025-01-01T00:00:00+01:00",
    updated_at="2025-01-01T00:00:00+01:00"
)

@pytest.mark.asyncio
@patch("app.services.regiojet_checker_service._fetch_regiojet_api", new_callable=AsyncMock)
async def test_check_route_availability_tickets_available(mock_fetch):
    """
    Test check_route_availability when the API indicates that tickets are available.
    """
    # Arrange
    # API returns a route object with free seats
    mock_fetch.return_value = {"id": 12345, "priceFrom": 150.0, "freeSeatsCount": 5}

    # Act
    is_available, details = await regiojet_checker_service.check_route_availability(MOCK_DB_ROUTE)

    # Assert
    assert is_available is True
    assert details is not None
    assert details["freeSeatsCount"] == 5
    assert details["priceFrom"] == 150.0
    assert "booking_link" in details
    mock_fetch.assert_awaited_once()

@pytest.mark.asyncio
@patch("app.services.regiojet_checker_service._fetch_regiojet_api", new_callable=AsyncMock)
async def test_check_route_availability_tickets_unavailable(mock_fetch):
    """
    Test check_route_availability when the API returns an error (e.g., 404 Not Found),
    indicating the specific route/price combo is not available.
    """
    # Arrange
    # API returns an error, which our client translates to HTTPException
    mock_fetch.side_effect = HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Act
    is_available, details = await regiojet_checker_service.check_route_availability(MOCK_DB_ROUTE)

    # Assert
    assert is_available is False
    assert details is None
    mock_fetch.assert_awaited_once()

@pytest.mark.asyncio
@patch("app.services.regiojet_checker_service._fetch_regiojet_api", new_callable=AsyncMock)
async def test_check_route_availability_api_error(mock_fetch, caplog):
    """
    Test that a non-404 HTTP error is caught, logged, and treated as 'unavailable'.
    """
    # Arrange
    error = HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server Down")
    mock_fetch.side_effect = error

    # Act
    is_available, details = await regiojet_checker_service.check_route_availability(MOCK_DB_ROUTE)

    # Assert
    assert is_available is False
    assert details is None
    mock_fetch.assert_awaited_once()
    # Check that the exception was logged
    assert "Unexpected error" in caplog.text
    assert "Server Down" in caplog.text

@pytest.mark.asyncio
@patch("app.services.regiojet_checker_service._fetch_regiojet_api", new_callable=AsyncMock)
async def test_check_route_availability_unexpected_success_response(mock_fetch):
    """
    Test check_route_availability with an unexpected (but successful) API response format.
    """
    # Arrange
    # API returns something other than a dictionary, which is unexpected for a success case
    mock_fetch.return_value = []

    # Act
    is_available, details = await regiojet_checker_service.check_route_availability(MOCK_DB_ROUTE)

    # Assert
    # If the format is unexpected, we should treat it as "not available" and log an error.
    assert is_available is False
    assert details is None
    mock_fetch.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.regiojet_checker_service._fetch_regiojet_api", new_callable=AsyncMock)
async def test_check_route_availability_zero_free_seats(mock_fetch):
    """
    Test check_route_availability when the API returns a successful response but with zero free seats.
    The service should return False and no details.
    """
    # Arrange
    mock_fetch.return_value = {"id": 12345, "priceFrom": 150.0, "freeSeatsCount": 0}

    # Act
    is_available, details = await regiojet_checker_service.check_route_availability(MOCK_DB_ROUTE)

    # Assert
    assert is_available is False
    assert details is None
    mock_fetch.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.regiojet_checker_service._fetch_regiojet_api", new_callable=AsyncMock)
async def test_check_route_availability_response_missing_seats_key(mock_fetch):
    """
    Test that a successful response missing the 'freeSeatsCount' key is handled gracefully
    by treating it as unavailable, per the service's current logic.
    """
    # Arrange
    mock_fetch.return_value = {"id": 12345, "priceFrom": 150.0}  # Missing 'freeSeatsCount'

    # Act
    is_available, details = await regiojet_checker_service.check_route_availability(MOCK_DB_ROUTE)

    # Assert
    assert is_available is False
    assert details is None
    mock_fetch.assert_awaited_once()
