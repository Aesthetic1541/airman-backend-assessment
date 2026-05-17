from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
from app.db.models import TrainingStatus


class TrainingCreate(BaseModel):
    sortie_id: int
    lesson_type: str


class TrainingSubmit(BaseModel):
    maneuver_score: int
    communication_score: int
    situational_awareness_score: int
    remarks: str

    @field_validator("maneuver_score", "communication_score", "situational_awareness_score")
    @classmethod
    def validate_score(cls, v, info):
        if not isinstance(v, int) or v < 1 or v > 5:
            raise ValueError(f"{info.field_name} must be an integer between 1 and 5")
        return v

    @field_validator("remarks")
    @classmethod
    def remarks_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Remarks cannot be empty during submission")
        return v


class TrainingReject(BaseModel):
    rejection_reason: str


class TrainingResponse(BaseModel):
    id: int
    sortie_id: int
    cadet_id: int
    instructor_id: int
    lesson_type: str
    maneuver_score: Optional[int]
    communication_score: Optional[int]
    situational_awareness_score: Optional[int]
    remarks: Optional[str]
    status: TrainingStatus
    submitted_at: Optional[datetime]
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}