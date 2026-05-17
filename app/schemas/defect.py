from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.db.models import DefectSeverity, DefectStatus


class DefectCreate(BaseModel):
    aircraft_id: int
    sortie_id: Optional[int] = None
    severity: DefectSeverity
    description: str


class DefectResolve(BaseModel):
    resolution_notes: Optional[str] = None


class DefectDefer(BaseModel):
    defer_reason: str


class DefectResponse(BaseModel):
    id: int
    aircraft_id: int
    sortie_id: Optional[int]
    reported_by: int
    severity: DefectSeverity
    description: str
    status: DefectStatus
    resolved_by: Optional[int]
    resolved_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}