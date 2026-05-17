from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import UnauthorizedError
from app.db.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise UnauthorizedError("Invalid or expired token")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    """FastAPI dependency: decode JWT and return the current user ORM object."""
    from app.db.models import User
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Token missing subject")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise UnauthorizedError("User not found")
    return user