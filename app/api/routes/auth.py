from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserResponse
from app.core.security import verify_password, create_access_token, get_current_user
from app.core.errors import UnauthorizedError

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")
    if not user.is_active:
        raise UnauthorizedError("Account is disabled")
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user