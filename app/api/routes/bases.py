from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import User, UserRole
from app.schemas.base_schema import BaseResponse
from app.core.security import get_current_user
from app.core.errors import NotFoundError, ForbiddenError
from app.db.models import Base_ as BaseModel

router = APIRouter(prefix="/bases", tags=["Bases"])


@router.get("", response_model=List[BaseResponse])
def list_bases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(BaseModel)
    if current_user.role != UserRole.ADMIN:
        q = q.filter(BaseModel.id == current_user.base_id)
    return q.all()


@router.get("/{base_id}", response_model=BaseResponse)
def get_base(
    base_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    base = db.query(BaseModel).filter(BaseModel.id == base_id).first()
    if not base:
        raise NotFoundError("Base not found")
    if current_user.role != UserRole.ADMIN and base.id != current_user.base_id:
        raise ForbiddenError("Access denied: base scope mismatch")
    return base