import datetime
from pydantic import BaseModel, Field
from typing import List, Optional

class AvailableRoute(BaseModel):
    """
    Schema representing an available route/connection for a specific date and origin/destination,
    as returned by the Regiojet API search.
    """
    routeId: str = Field(..., description="Regiojet's internal ID for this specific route instance")
    departureTime: datetime.datetime = Field(..., description="Full departure datetime with timezone")
    arrivalTime: datetime.datetime = Field(..., description="Full arrival datetime with timezone")
    freeSeatsCount: int = Field(..., description="Number of free seats currently available")
    vehicleTypes: List[str] = Field(..., description="List of vehicle types on this route (e.g., ['BUS'], ['TRAIN'])")
    fromStationId: str = Field(..., description="Specific station ID for departure on this route instance")
    toStationId: str = Field(..., description="Specific station ID for arrival on this route instance")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "routeId": "7558895449",
                    "departureTime": "2024-08-15T10:30:00+02:00",
                    "arrivalTime": "2024-08-15T13:00:00+02:00",
                    "freeSeatsCount": 5,
                    "vehicleTypes": ["TRAIN"],
                    "fromStationId": "3088864001", # Brno hl.n.
                    "toStationId": "372825000" # Praha hl.n.
                }
            ]
        }
    }
