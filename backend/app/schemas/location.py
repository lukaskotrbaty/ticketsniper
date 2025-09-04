from pydantic import BaseModel, Field, field_validator
from typing import List, Literal

class Location(BaseModel):
    """
    Schema representing a location (city or station) from Regiojet API.
    """
    id: str = Field(..., description="Regiojet's internal ID for the location")
    name: str = Field(..., description="Human-readable name of the location")
    type: Literal["CITY", "STATION"] = Field(..., description="Type of location, e.g., 'CITY', 'STATION'")
    normalized_name: str = Field(..., description="Normalized name of the location")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "10202000",
                    "name": "Frýdek-Místek",
                    "type": "CITY",
                    "normalized_name": "frydek-mistek"
                },
                {
                    "id": "372825000",
                    "name": "Praha hl.n.",
                    "type": "STATION",
                    "normalized_name": "praha hl.n."
                }
            ]
        }
    }
