from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # detect stale connections
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yield a DB session and ensure it closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()