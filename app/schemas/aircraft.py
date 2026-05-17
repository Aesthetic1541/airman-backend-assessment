from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.db.models import AircraftStatus


class AircraftCreate(BaseModel):
    registration: str
    aircraft_type: str
    base_id: int
    tbo_remaining_hours: Optional[float] = None


class AircraftResponse(BaseModel):
    id: int
    registration: str
    aircraft_type: str
    base_id: int
    status: AircraftStatus
    tbo_remaining_hours: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


class GroundRequest(BaseModel):
    reason: Optional[str] = None