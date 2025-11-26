# Design Document

## Overview

Systematically debug and fix all backend API endpoints to ensure the dashboard displays data correctly. The main issues are:
1. Service layer returning Pydantic models that API layer tries to treat as dictionaries
2. Missing or incomplete data handling
3. CORS errors when backend crashes

## Architecture

The backend follows a layered architecture:
```
Frontend (React) → API Layer (FastAPI routes) → Service Layer (business logic) → Database (PostgreSQL)
```

**Problem Pattern**: Service functions return Pydantic models, but API routes try to use dictionary methods like `.get()` on them.

**Solution Pattern**: Either:
- Return dictionaries from services, OR
- Return Pydantic models directly from API routes without manipulation

## Components and Interfaces

### 1. Climate Service (`app/services/climate_service.py`)
- `get_climate_timeseries()` - Returns time series data
- `calculate_anomalies()` - Calculates statistical anomalies
- `get_correlations()` - Calculates variable correlations

### 2. Trigger Service (`app/services/trigger_service.py` or similar)
- `get_triggers()` - Returns trigger events from database
- Needs to handle filtering, pagination

### 3. Dashboard Service (`app/services/dashboard_service.py`)
- `get_executive_kpis()` - Calculates KPIs
- `get_loss_ratio_trend()` - Calculates trends
- `get_sustainability_status()` - Calculates sustainability metrics

### 4. Model Service (`app/services/model_service.py` or in models API)
- `get_model_metrics()` - Returns model performance data
- Needs to handle null/missing values

## Data Models

All Pydantic models should be reviewed to ensure:
- Optional fields use `Optional[type]` or `type | None`
- Default values for fields that might be missing
- Proper serialization configuration

## Error Handling

Add try-catch blocks in API routes to:
1. Catch service layer errors
2. Return proper HTTP status codes
3. Include CORS headers even on errors
4. Log errors for debugging

## Testing Strategy

Manual testing approach:
1. Test each endpoint individually using curl or browser
2. Check backend logs for errors
3. Verify data format matches frontend expectations
4. Test with missing/null data scenarios
