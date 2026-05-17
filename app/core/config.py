from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://airman:airman_secret@localhost:5432/skynet"
    SECRET_KEY: str = "change-me-in-production-at-least-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()