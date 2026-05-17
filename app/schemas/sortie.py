from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.db.models import SortieStatus


class SortieCreate(BaseModel):
    sortie_number: str
    cadet_id: int
    instructor_id: int
    aircraft_id: int
    base_id: int
    lesson_type: str
    scheduled_start: datetime
    scheduled_end: datetime


class SortieResponse(BaseModel):
    id: int
    sortie_number: str
    cadet_id: int
    instructor_id: int
    aircraft_id: int
    base_id: int
    lesson_type: str
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    status: SortieStatus
    delay_minutes: int
    cancel_reason: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class CancelRequest(BaseModel):
    reason: str