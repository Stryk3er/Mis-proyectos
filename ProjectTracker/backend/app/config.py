"""
Application settings loaded from environment variables.
Copy .env.example to .env and adjust values before running.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "ProjectTracker"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str = "sqlite:///./projecttracker.db"
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
