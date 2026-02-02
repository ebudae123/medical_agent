from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres123@localhost/nightingale"
    
    # Gemini API
    google_api_key: str
    gemini_model: str = "gemini-2.5-pro"
    
    # Redis (for WebSocket scaling - optional for now)
    redis_url: str = "redis://localhost:6379"
    
    # Application
    app_name: str = "Nightingale AI Medical Assistant"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
