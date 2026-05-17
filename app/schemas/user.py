from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.db.models import UserRole


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    base_id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}