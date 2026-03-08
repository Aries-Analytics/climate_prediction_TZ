from pydantic_settings import BaseSettings
from typing import List, Optional
import json

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/climate_dev"
    
    # Authentication
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS
    ALLOWED_ORIGINS: str = '["http://localhost:3000"]'
    
    # File Paths
    OUTPUTS_DIR: str = "/outputs"
    MODELS_DIR: str = "/outputs/models"
    DATA_DIR: Optional[str] = "data"
    RAW_DATA_DIR: Optional[str] = "/raw"
    PROCESSED_DATA_DIR: Optional[str] = "/processed"
    OUTPUT_DIR: Optional[str] = "outputs"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "logs/pipeline.log"
    
    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 300  # 5 minutes default
    CACHE_ENABLED: bool = True
    
    # Google Cloud / Earth Engine
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    
    # API Endpoints
    NASA_API_URL: Optional[str] = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    NASA_API_KEY: Optional[str] = None
    ERA5_API_KEY: Optional[str] = None
    CHIRPS_BASE_URL: Optional[str] = "https://data.chc.ucsb.edu/products/CHIRPS-2.0"
    NDVI_SOURCE_URL: Optional[str] = None
    OCEAN_INDICES_SOURCE_URL: Optional[str] = None
    
    # Project Constants
    DEFAULT_REGION: Optional[str] = "Tanzania"
    DEFAULT_CRS: Optional[str] = "EPSG:4326"
    
    # Pipeline Configuration
    PIPELINE_SCHEDULE: str = "0 6 * * *"
    PIPELINE_TIMEZONE: str = "UTC"
    
    # Alert Configuration
    ALERT_EMAIL_ENABLED: bool = False
    ALERT_EMAIL_SMTP_HOST: Optional[str] = None
    ALERT_EMAIL_SMTP_PORT: int = 587
    ALERT_EMAIL_FROM: Optional[str] = None
    ALERT_EMAIL_RECIPIENTS: Optional[str] = None
    ALERT_EMAIL_USERNAME: Optional[str] = None
    ALERT_EMAIL_PASSWORD: Optional[str] = None
    ALERT_SLACK_ENABLED: bool = False
    ALERT_SLACK_WEBHOOK_URL: Optional[str] = None
    
    # Retry Configuration
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_INITIAL_DELAY: float = 2.0
    RETRY_BACKOFF_FACTOR: float = 2.0
    
    # Monitoring
    MONITORING_METRICS_PORT: int = 9090
    MONITORING_HEALTH_PORT: int = 8080
    
    # Data Quality
    DATA_STALENESS_THRESHOLD_DAYS: int = 7
    FORECAST_STALENESS_THRESHOLD_DAYS: int = 7
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields in .env
    
    def get_allowed_origins(self) -> List[str]:
        """Parse ALLOWED_ORIGINS from JSON string"""
        try:
            return json.loads(self.ALLOWED_ORIGINS)
        except:
            return ["http://localhost:3000"]

settings = Settings()
