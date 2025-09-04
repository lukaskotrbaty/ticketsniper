import time
from typing import Dict, Optional, Any
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError: # Fallback for Python < 3.9 (though project is 3.10)
    from backports.zoneinfo import ZoneInfo # type: ignore

from sqladmin import ModelView

from app.db.models.user import User
from app.db.models.route import MonitoredRoute, UserRouteSubscription, RouteStatusEnum
from app.core.config import settings # For settings.LOCATION_CACHE_TTL_SECONDS
from app.services.regiojet_data_service import _get_locations_from_cache_sync # Use service
from app.schemas.location import Location # For type hinting if needed, service returns List[Location]


# Module-level cache for location names
_location_name_cache: Optional[Dict[str, str]] = None
_location_cache_last_updated: float = 0.0
# Use TTL from settings for the in-memory cache as well, if locations are static
_IN_MEMORY_LOCATION_CACHE_TTL_SECONDS: int = settings.LOCATION_CACHE_TTL_SECONDS


def _fetch_and_cache_location_names() -> Dict[str, str]:
    global _location_name_cache, _location_cache_last_updated
    current_time = time.time()

    if _location_name_cache is not None and \
       (current_time - _location_cache_last_updated) < _IN_MEMORY_LOCATION_CACHE_TTL_SECONDS:
        return _location_name_cache

    location_map: Dict[str, str] = {}
    try:
        # Use the sync service function to get validated Location objects
        locations: Optional[list[Location]] = _get_locations_from_cache_sync()
        
        if locations:
            for loc_model in locations:
                location_map[str(loc_model.id)] = loc_model.name
        
        _location_name_cache = location_map
        _location_cache_last_updated = current_time
    except Exception as e:
        # Log error from calling the service function or processing its result
        print(f"Error using _get_locations_from_cache_sync or processing its result: {e}") # Basic logging
        # Return stale cache if available, otherwise empty map
        return _location_name_cache if _location_name_cache is not None else {}
    
    return _location_name_cache if _location_name_cache is not None else {}


def format_from_location_name(model: Any, attribute_name: str) -> str:
    location_map = _fetch_and_cache_location_names()
    location_id = str(getattr(model, "from_location_id", ""))
    return location_map.get(location_id, location_id) # Fallback to ID if name not found

def format_to_location_name(model: Any, attribute_name: str) -> str:
    location_map = _fetch_and_cache_location_names()
    location_id = str(getattr(model, "to_location_id", ""))
    return location_map.get(location_id, location_id) # Fallback to ID if name not found

PRAGUE_TZ = ZoneInfo("Europe/Prague")

def _format_datetime_prague(dt_value: Optional[datetime]) -> str:
    if dt_value is None:
        return ""
    # Assuming dt_value from DB is timezone-aware (UTC)
    if dt_value.tzinfo is None:
        # If it's naive, assume UTC from DB and make it aware
        dt_value = dt_value.replace(tzinfo=ZoneInfo("UTC"))
    
    dt_prague = dt_value.astimezone(PRAGUE_TZ)
    return dt_prague.strftime("%Y-%m-%d %H:%M:%S")


def format_departure_datetime_prague(model: Any, attribute_name: str) -> str:
    dt_value = getattr(model, "departure_datetime", None)
    return _format_datetime_prague(dt_value)

def format_arrival_datetime_prague(model: Any, attribute_name: str) -> str:
    dt_value = getattr(model, "arrival_datetime", None)
    return _format_datetime_prague(dt_value)


class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    column_list = [
        User.id,
        User.email,
        User.is_verified,
        User.created_at,
        User.updated_at,
    ]
    column_searchable_list = [User.email]
    column_sortable_list = [
        User.id,
        User.email,
        User.is_verified,
        User.created_at,
        User.updated_at,
    ]
    # Exclude hashed_password from forms for security
    # form_excluded_columns = [User.hashed_password, User.subscriptions] # Cannot be used with form_columns
    # Define all editable fields in form_columns
    form_columns = [
        User.email,
        User.is_verified,
        # Add other fields if they should be editable, e.g., User.id (though usually not)
        # User.created_at, User.updated_at are typically read-only and handled by the DB.
    ]


class MonitoredRouteAdmin(ModelView, model=MonitoredRoute):
    name = "Monitored Route"
    name_plural = "Monitored Routes"
    icon = "fa-solid fa-route"
    column_list = [
        MonitoredRoute.id,
        MonitoredRoute.regiojet_route_id,
        "from_location_name", # Virtual column
        MonitoredRoute.from_location_type,
        "to_location_name",   # Virtual column
        MonitoredRoute.to_location_type,
        # MonitoredRoute.departure_datetime, # Will be formatted
        # MonitoredRoute.arrival_datetime,   # Will be formatted
        "departure_datetime_prague",
        "arrival_datetime_prague",
        MonitoredRoute.status,
        MonitoredRoute.last_checked_at, # Consider formatting this too if needed
        MonitoredRoute.created_at,
        MonitoredRoute.updated_at,
    ]
    column_labels = {
        "from_location_name": "From Location",
        "to_location_name": "To Location",
        MonitoredRoute.from_location_type: "From Type",
        MonitoredRoute.to_location_type: "To Type",
        "departure_datetime_prague": "Departure (Prague)",
        "arrival_datetime_prague": "Arrival (Prague)",
    }
    column_formatters = {
        "from_location_name": format_from_location_name,
        "to_location_name": format_to_location_name,
        "departure_datetime_prague": format_departure_datetime_prague,
        "arrival_datetime_prague": format_arrival_datetime_prague,
        # If last_checked_at also needs formatting:
        # MonitoredRoute.last_checked_at: lambda m, a: _format_datetime_prague(getattr(m, 'last_checked_at', None)),
    }
    # Searching by formatted/virtual columns is not directly supported by default.
    # We keep search on the original ID fields.
    column_searchable_list = [
        MonitoredRoute.regiojet_route_id,
        MonitoredRoute.from_location_id, # Search still uses the ID
        MonitoredRoute.to_location_id,   # Search still uses the ID
    ]
    # Sorting by formatted/virtual columns is not directly supported by default.
    # We sort by the original datetime columns.
    column_sortable_list = [
        MonitoredRoute.id,
        MonitoredRoute.departure_datetime, # Sorts by original UTC datetime
        MonitoredRoute.arrival_datetime,   # Sorts by original UTC datetime
        MonitoredRoute.status,
        MonitoredRoute.last_checked_at, # Sorts by original UTC datetime
        MonitoredRoute.created_at,
        MonitoredRoute.updated_at,
    ]
    # form_excluded_columns = [MonitoredRoute.subscribers] # Cannot be used with form_columns
    # Define all editable fields in form_columns
    form_columns = [
        MonitoredRoute.regiojet_route_id,
        MonitoredRoute.from_location_id,
        MonitoredRoute.from_location_type,
        MonitoredRoute.to_location_id,
        MonitoredRoute.to_location_type,
        MonitoredRoute.departure_datetime,
        MonitoredRoute.arrival_datetime,
        MonitoredRoute.status, # Enum should be handled correctly by SQLAdmin
        MonitoredRoute.last_checked_at,
    ]


class UserRouteSubscriptionAdmin(ModelView, model=UserRouteSubscription):
    name = "User Subscription"
    name_plural = "User Subscriptions"
    icon = "fa-solid fa-link"
    # Use relationships for better readability in the list
    column_list = [
        "user.email",  # Accesses User.email via the 'user' relationship
        "route.id",    # Accesses MonitoredRoute.id via the 'route' relationship
        "route.regiojet_route_id", # Accesses MonitoredRoute.regiojet_route_id
        UserRouteSubscription.created_at,
    ]
    # Define how these relational columns should be named in the UI
    column_labels = {
        "user.email": "User Email",
        "route.id": "Route ID",
        "route.regiojet_route_id": "Regiojet Route ID"
    }
    # Allow searching by user email or route ID
    column_searchable_list = ["user.email", "route.regiojet_route_id"]
    column_sortable_list = [UserRouteSubscription.created_at, "user.email", "route.id"]
    
    # Usually, junction tables like this are managed via the parent tables,
    # but if direct editing is needed:
    form_columns = [
        UserRouteSubscription.user, # Allows selecting a User
        UserRouteSubscription.route # Allows selecting a MonitoredRoute
    ]


admin_views_to_register = [UserAdmin, MonitoredRouteAdmin, UserRouteSubscriptionAdmin]
