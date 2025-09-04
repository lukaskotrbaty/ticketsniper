import pytest
import datetime
import json
from pathlib import Path

from app.services.regiojet_data_parser import (
    _parse_locations_response,
    _parse_single_route,
    ParsingError,
)
from app.schemas.available_route import AvailableRoute
from app.schemas.location import Location


# --- Fixtures ---

@pytest.fixture
def locations_api_response_valid() -> list:
    """Loads valid locations fixture data matching the real API structure."""
    path = Path(__file__).parent.parent / "fixtures/locations.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def routes_api_response_valid() -> dict:
    """Loads valid routes fixture data matching the real API structure."""
    path = Path(__file__).parent.parent / "fixtures/available_routes.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Tests for _parse_locations_response ---

def test_parse_locations_success(locations_api_response_valid):
    """Test parsing a valid locations API response."""
    parsed = _parse_locations_response(locations_api_response_valid)
    
    assert isinstance(parsed, list)
    assert len(parsed) == 7  # 3 cities + 4 stations
    
    # Validate with Pydantic models
    validated_locations = [Location.model_validate(p) for p in parsed]
    
    assert validated_locations[0].id == "10202000"
    assert validated_locations[0].name == "Praha"
    assert validated_locations[0].type == "CITY"
    
    assert validated_locations[1].id == "372825000"
    assert validated_locations[1].name == "Praha hl.n."
    assert validated_locations[1].type == "STATION"

    assert validated_locations[6].id == "1841058000"
    assert validated_locations[6].name == "Bratislava,,AS" # As per fixture
    assert validated_locations[6].type == "STATION"


def test_parse_locations_invalid_top_level_format():
    """Test parsing when the top level is not a list."""
    with pytest.raises(ParsingError, match="Received unexpected data format from Regiojet API"):
        _parse_locations_response({"not_a": "list"})


@pytest.mark.parametrize("bad_data, expected_len, description", [
    ([{"country": "CZ", "cities": [None, {"id": 1, "name": "City1"}]}], 1, "Invalid city entry"), # Only City1 is parsed
    ([{"country": "CZ", "cities": [{"id": 1, "name": "C1", "stations": ["invalid", {"id": 2, "name": "S2"}]}]}], 2, "Invalid station entry"), # C1 + S2
    ([{"country": "CZ", "cities": [{"name": "C1"}, {"id": 2, "name": "C2"}]}], 1, "Missing city id"), # Only C2
    ([{"country": "CZ", "cities": [{"id": 1, "stations": [{"name": "S1"}]}]}], 0, "Missing city name"), # City is skipped, so are its stations
])
def test_parse_locations_robustness(bad_data, expected_len, description):
    """Test that parser handles various forms of malformed data gracefully."""
    parsed = _parse_locations_response(bad_data)
    assert len(parsed) == expected_len, f"Failed on: {description}"


# --- Tests for _parse_single_route ---

def test_parse_single_route_success(routes_api_response_valid):
    """Test parsing a valid single route for the correct date."""
    route_data = routes_api_response_valid["routes"][0]
    requested_date = datetime.date(2025, 8, 15)
    
    parsed = _parse_single_route(route_data, requested_date)
    
    assert parsed is not None
    validated_route = AvailableRoute.model_validate(parsed)
    
    assert validated_route.routeId == str(route_data["id"])
    assert validated_route.departureTime.time() == datetime.time(10, 30)
    assert validated_route.arrivalTime.time() == datetime.time(13, 0)
    assert validated_route.freeSeatsCount == route_data["freeSeatsCount"]
    assert validated_route.vehicleTypes == route_data["vehicleTypes"]
    assert validated_route.fromStationId == str(route_data["departureStationId"])
    assert validated_route.toStationId == str(route_data["arrivalStationId"])


def test_parse_single_route_returns_none_for_wrong_date(routes_api_response_valid):
    """Test that parsing a route for a different date returns None."""
    route_data = routes_api_response_valid["routes"][0]
    requested_date = datetime.date(2025, 8, 16)  # A day after
    
    parsed = _parse_single_route(route_data, requested_date)
    
    assert parsed is None


@pytest.mark.parametrize("bad_route_data, description", [
    ("not_a_dict", "Input is not a dictionary"),
    ({"freeSeatsCount": None}, "Missing essential keys (value is None)"),
    ({"departureTime": "invalid-time"}, "Invalid time format"),
    ({}, "Completely empty dict"),
])
def test_parse_single_route_returns_none_for_bad_data(bad_route_data, description):
    """Test that parser returns None for various malformed inputs."""
    # A base of valid data
    base_data = {
        "id": 123, "departureTime": "2025-08-15T10:00:00", "arrivalTime": "2025-08-15T12:00:00",
        "freeSeatsCount": 1, "vehicleTypes": [], "departureStationId": 1, "arrivalStationId": 2
    }
    
    # For dicts, create a fresh copy and then manipulate
    if isinstance(bad_route_data, dict):
        final_data = base_data.copy()
        # If the test case is to check for missing keys, delete them
        if "Completely empty" in description:
            final_data = {}
        # If the test case is to check for None values or invalid formats, update the dict
        else:
            final_data.update(bad_route_data)
            # Special case for testing missing key
            if "Missing essential keys" in description:
                 del final_data["freeSeatsCount"]

    else:
        final_data = bad_route_data

    parsed = _parse_single_route(final_data, datetime.date(2025, 8, 15))
    assert parsed is None, f"Failed on: {description}"
