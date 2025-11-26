from pydantic_settings import BaseSettings
from typing import List
import json

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/climate_db"
    
    # Authentication
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # CORS
    ALLOWED_ORIGINS: str = '["http://localhost:3000"]'
    
    # File Paths
    OUTPUTS_DIR: str = "../outputs"
    MODELS_DIR: str = "../outputs/models"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 300  # 5 minutes default
    CACHE_ENABLED: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_allowed_origins(self) -> List[str]:
        """Parse ALLOWED_ORIGINS from JSON string"""
        try:
            return json.loads(self.ALLOWED_ORIGINS)
        except:
            return ["http://localhost:3000"]

settings = Settings()
