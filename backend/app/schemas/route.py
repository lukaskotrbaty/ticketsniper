from pydantic import BaseModel, Field
from datetime import date, time, datetime
from typing import List, Optional, Dict, Any # Added Dict, Any


# Base schema for route data, used for internal representation
class RouteBase(BaseModel):
    regiojet_route_id: str
    from_location_id: str
    from_location_type: str
    to_location_id: str
    to_location_type: str
    departure_datetime: datetime
    arrival_datetime: Optional[datetime] = None
    status: str = "MONITORING"


# Schema for creating a route in the database (internal use)
class RouteCreate(RouteBase):
    pass


# Schema for reading a route from the database (represents the DB model)
class Route(RouteBase):
    id: int
    last_checked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


# Schema for receiving monitoring request data from the frontend
class RouteMonitorRequest(BaseModel):
    from_location_id: str = Field(..., description="Regiojet ID of the origin location")
    from_location_type: str = Field(..., description="Type of the origin location ('CITY' or 'STATION')")
    to_location_id: str = Field(..., description="Regiojet ID of the destination location")
    to_location_type: str = Field(..., description="Type of the destination location ('CITY' or 'STATION')")
    departure_datetime: datetime = Field(..., description="Specific departure datetime (ISO format with timezone)")
    arrival_datetime: Optional[datetime] = Field(None, description="Specific arrival datetime (ISO format with timezone, optional)")
    regiojet_route_id: str = Field(..., description="Regiojet's unique ID for the specific route instance")

    # Pydantic v2 configuration
    model_config = {
        "json_schema_extra": {
            "example": {
                "from_location_id": "10202003",
                "from_location_type": "STATION",
                "to_location_id": "10202000",
                "to_location_type": "STATION",
                "departure_datetime": "2024-08-15T10:30:00+02:00",
                "arrival_datetime": "2024-08-15T13:45:00+02:00",
                "regiojet_route_id": "1234567890"
            }
        }
    }


# Schema for returning information about a monitored route to the frontend
class MonitoredRouteInfo(BaseModel):
    id: int
    route_id: str
    from_location_id: str
    from_location_type: str
    to_location_id: str
    to_location_type: str
    from_location_name: Optional[str] = None
    to_location_name: Optional[str] = None
    departure_datetime: datetime
    arrival_datetime: Optional[datetime] = None
    status: str
    created_at: datetime  # Subscription creation time

    model_config = {
        "from_attributes": True
    }


# Schema for the response of the POST /monitor endpoint (Task 10)
class RouteMonitorResponse(BaseModel):
    message: str
    available: bool
    details: Optional[Dict[str, Any]] = None


# Schema for the response of the POST /monitored-routes/{db_id}/restart endpoint
class RouteRestartResponse(BaseModel):
    message: str
    restarted: bool # Indicates if monitoring was actually restarted (i.e., tickets were not available)
    details: Optional[Dict[str, Any]] = None # Optional details if tickets were still available
