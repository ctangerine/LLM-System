import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the project root directory (be folder)
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    CELERY_BROKER_URL: str
    GOOGLE_API_KEY: str
    REDIS_URL: str
    LANGSMITH_TRACING: bool
    LANGSMITH_ENDPOINT: str
    LANGSMITH_API_KEY: str
    LANGSMITH_PROJECT: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding='utf-8'
    )

settings = Settings()

LANGSMITH_TRACING = settings.LANGSMITH_TRACING
LANGSMITH_ENDPOINT = settings.LANGSMITH_ENDPOINT
LANGSMITH_API_KEY = settings.LANGSMITH_API_KEY
LANGSMITH_PROJECT = settings.LANGSMITH_PROJECT
GOOGLE_API_KEY = settings.GOOGLE_API_KEY

