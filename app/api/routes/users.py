from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import User, UserRole
from app.schemas.user import UserResponse
from app.core.security import get_current_user
from app.core.errors import NotFoundError, ForbiddenError

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admins see all users; others see users in their own base."""
    q = db.query(User)
    if current_user.role != UserRole.ADMIN:
        q = q.filter(User.base_id == current_user.base_id)
    return q.all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User not found")
    if current_user.role != UserRole.ADMIN and user.base_id != current_user.base_id:
        raise ForbiddenError("Access denied: base scope mismatch")
    return user