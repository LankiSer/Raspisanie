"""Application configuration and settings."""

from typing import Optional, List
from pydantic import field_validator
from pydantic_settings import BaseSettings
import secrets


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str
    
    # JWT
    JWT_SECRET: str = secrets.token_urlsafe(32)
    JWT_EXPIRES: int = 3600
    JWT_ALGORITHM: str = "HS256"
    
    # Organization defaults
    ORG_DEFAULT_LOCALE: str = "ru"
    TZ: str = "Europe/Moscow"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Schedule SaaS"
    PROJECT_VERSION: str = "0.1.0"
    
    # CORS
    CORS_ORIGINS: str = "*"
    
    @field_validator('CORS_ORIGINS')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # App settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Schedule generation
    MAX_GENERATION_JOBS_PER_ORG: int = 5
    GENERATION_TIMEOUT_SECONDS: int = 300
    
    class Config:
        env_file = ".env"
        extra = "ignore"
        case_sensitive = True


settings = Settings()
