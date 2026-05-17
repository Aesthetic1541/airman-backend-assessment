from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.db.models import UserRole


class AuditLogResponse(BaseModel):
    id: int
    actor_id: int
    actor_role: UserRole
    action: str
    entity_type: str
    entity_id: int
    old_value: Optional[str]
    new_value: Optional[str]
    reason: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}