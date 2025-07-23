# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    CELERY_BROKER_URL: str
    GOOGLE_API_KEY: str
    REDIS_URL: str
    LANGSMITH_TRACING: bool
    LANGSMITH_ENDPOINT: str
    LANGSMITH_API_KEY: str
    LANGSMITH_PROJECT: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

LANGSMITH_TRACING = settings.LANGSMITH_TRACING
LANGSMITH_ENDPOINT = settings.LANGSMITH_ENDPOINT
LANGSMITH_API_KEY = settings.LANGSMITH_API_KEY
LANGSMITH_PROJECT = settings.LANGSMITH_PROJECT
GOOGLE_API_KEY = settings.GOOGLE_API_KEY
