from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
from app.core.exceptions import APIException
from app.core.error_handlers import (
    api_exception_handler,
    validation_exception_handler,
    database_exception_handler,
    general_exception_handler
)
from app.middleware.audit import AuditMiddleware
from app.middleware.security import (
    RateLimitMiddleware,
    InputSanitizationMiddleware,
    SecurityHeadersMiddleware
)
from app.api import auth, dashboard, models, triggers, climate, risk, admin, forecasts, pipeline, geo, locations, climate_forecasts, claims
from app.core.cache import cache_manager

app = FastAPI(
    title="Tanzania Climate Prediction API",
    description="API for climate insights, ML model monitoring, and insurance triggers",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    await cache_manager.initialize()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(InputSanitizationMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

# Add audit logging middleware
app.add_middleware(AuditMiddleware)

# Register exception handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(triggers.router, prefix="/api")
app.include_router(climate.router, prefix="/api")
app.include_router(risk.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(forecasts.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")
app.include_router(locations.router, prefix="/api")
app.include_router(climate_forecasts.router, prefix="/api")
app.include_router(claims.router, prefix="/api")
app.include_router(geo.router)

@app.get("/")
async def root():
    return {"message": "Tanzania Climate Prediction API", "status": "running"}

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "api"}

@app.get("/health/ready")
async def readiness_check():
    """Readiness check with database connectivity"""
    from app.core.database import SessionLocal
    from sqlalchemy import text
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not_ready", "database": "disconnected", "error": str(e)}
