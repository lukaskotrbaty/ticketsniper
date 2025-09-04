import datetime
import logging
import unicodedata
from typing import List, Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_string(text: Optional[str]) -> str:
    """
    Normalizes a string by converting to lowercase and removing diacritics.
    Returns an empty string if input is None.
    """
    if text is None:
        return ""
    # NFKD normal form decomposes characters into base characters and combining marks
    # Encode to ascii ignoring errors removes the combining marks
    # Decode back to utf-8
    return unicodedata.normalize('NFKD', text.lower()).encode('ascii', 'ignore').decode('utf-8')

class ParsingError(Exception):
    """ Custom exception for critical parsing errors. """
    pass

def _parse_locations_response(api_data: Any) -> List[Dict[str, Any]]:
    """
    Parses the raw response from the /consts/locations endpoint.
    Expected input: List[Country] -> List[City] -> List[Station]
    Returns a flat list of location dictionaries including a normalized_name field.
    Logs warnings for invalid entries but attempts to continue.
    Raises ParsingError if the top-level structure is not a list.
    """
    if not isinstance(api_data, list):
        logger.error(f"Unexpected API response type for locations: {type(api_data)}. Expected list.")
        raise ParsingError("Received unexpected data format from Regiojet API (locations).")

    parsed_locations: List[Dict[str, Any]] = []
    for country in api_data:
        if not isinstance(country, dict):
            logger.warning(f"Expected country entry to be a dict, but got {type(country)}. Skipping.")
            continue

        cities_data = country.get("cities", [])
        if not isinstance(cities_data, list):
            logger.warning(f"Expected 'cities' key to be a list for country {country.get('code')}, but got {type(cities_data)}. Skipping cities.")
            continue

        for city in cities_data:
            if not isinstance(city, dict):
                logger.warning(f"Expected city entry to be a dict in country {country.get('code')}, but got {type(city)}. Skipping.")
                continue

            # Add city itself
            city_id = city.get("id")
            city_name = city.get("name")
            if city_id is not None and city_name is not None:
                normalized_city_name = normalize_string(city_name)
                parsed_locations.append({
                    "id": str(city_id),
                    "name": city_name,
                    "type": "CITY",
                    "normalized_name": normalized_city_name
                })
            else:
                 logger.warning(f"Skipping city due to missing id or name: {city}")
                 continue # Skip city if essential info missing

            # Add stations within the city
            stations_data = city.get("stations", [])
            if not isinstance(stations_data, list):
                logger.warning(f"Expected 'stations' key to be a list for city {city_name}, but got {type(stations_data)}. Skipping stations.")
                continue

            for station in stations_data:
                if not isinstance(station, dict):
                    logger.warning(f"Expected station entry to be a dict for city {city_name}, but got {type(station)}. Skipping station.")
                    continue

                station_id = station.get("id")
                # Use 'fullname' for stations, fallback to 'name' if 'fullname' is missing
                station_name = station.get("fullname") or station.get("name")
                if station_id is not None and station_name is not None:
                    normalized_station_name = normalize_string(station_name)
                    parsed_locations.append({
                        "id": str(station_id),
                        "name": station_name,
                        "type": "STATION",
                        "normalized_name": normalized_station_name
                    })
                else:
                    logger.warning(f"Skipping station due to missing id or name: {station}")

    return parsed_locations


def _parse_single_route(route_data: Dict, requested_date: datetime.date) -> Optional[Dict[str, Any]]:
    """
    Parses a single route dictionary from the /routes/search/simple response.
    Checks if the departure date matches the requested date.
    Returns a dictionary ready for AvailableRoute Pydantic validation, or None if invalid/skipped.
    """
    if not isinstance(route_data, dict):
        logger.warning(f"Expected route entry to be a dict, but got {type(route_data)}. Skipping.")
        return None

    route_id_str = str(route_data.get("id", "UNKNOWN"))

    try:
        # Extract necessary fields, checking for None early
        departure_station_id = route_data.get("departureStationId")
        arrival_station_id = route_data.get("arrivalStationId")
        departure_dt_str = route_data.get("departureTime")
        arrival_dt_str = route_data.get("arrivalTime")
        free_seats = route_data.get("freeSeatsCount")
        vehicle_types = route_data.get("vehicleTypes")

        if None in [departure_station_id, arrival_station_id, departure_dt_str, arrival_dt_str, free_seats, vehicle_types, route_data.get("id")]:
            logger.warning(f"Skipping route {route_id_str} due to missing essential fields.")
            return None

        # Parse times with specific error handling
        try:
            departure_dt = datetime.datetime.fromisoformat(departure_dt_str)
        except ValueError as e_dep:
            logger.warning(f"Skipping route {route_id_str} due to invalid departure time format: {repr(e_dep)}. Value: {departure_dt_str!r}")
            return None
        try:
            arrival_dt = datetime.datetime.fromisoformat(arrival_dt_str)
        except ValueError as e_arr:
             logger.warning(f"Skipping route {route_id_str} due to invalid arrival time format: {repr(e_arr)}. Value: {arrival_dt_str!r}")
             return None

        # Check date match
        if departure_dt.date() != requested_date:
            return None # Skip route if it's not for the requested date

        # Return dictionary ready for validation
        return {
            "routeId": route_id_str,
            "departureTime": departure_dt, # Return full datetime object
            "arrivalTime": arrival_dt,     # Return full datetime object
            "freeSeatsCount": int(free_seats),
            "vehicleTypes": list(vehicle_types),
            "fromStationId": str(departure_station_id),
            "toStationId": str(arrival_station_id)
        }

    except (TypeError, KeyError, AttributeError) as e:
        # Catch other potential errors during processing this specific route
        logger.warning(f"Skipping route {route_id_str} due to processing error: {repr(e)}. Data: {route_data}")
        return None
    except Exception as e:
        # Catch unexpected errors for this route
        logger.exception(f"Unexpected error processing route {route_id_str}: {repr(e)}. Data: {route_data}")
        return None # Skip on unexpected errors as well
