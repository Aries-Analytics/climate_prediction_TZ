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
from app.api import auth, dashboard, models, triggers, climate, risk, admin

app = FastAPI(
    title="Tanzania Climate Prediction API",
    description="API for climate insights, ML model monitoring, and insurance triggers",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/")
async def root():
    return {"message": "Tanzania Climate Prediction API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
