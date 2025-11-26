# Design Document: Dashboard Data Integration

## Overview

This design outlines the technical approach for integrating real climate prediction data from the completed pipeline into the Interactive Dashboard System. The integration involves creating data loading scripts, configuring services, and ensuring the dashboard displays actual data from the Tanzania Climate Prediction system.

**Key Components:**
1. Data loading scripts (Python) to populate PostgreSQL database
2. Backend API service (FastAPI) serving data endpoints
3. Frontend dashboard (React) displaying visualizations
4. Docker Compose orchestration for all services
5. Verification and monitoring tools

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Loading Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Climate Data │  │ Trigger Data │  │ Model Metrics│      │
│  │   Loader     │  │    Loader    │  │    Loader    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            ▼                                 │
│                   ┌─────────────────┐                        │
│                   │   PostgreSQL    │                        │
│                   │    Database     │                        │
│                   └────────┬────────┘                        │
└────────────────────────────┼──────────────────────────────────┘
                             │
┌────────────────────────────┼──────────────────────────────────┐
│                     Backend API Layer                         │
│                   ┌────────┴────────┐                         │
│                   │   FastAPI       │                         │
│                   │   Application   │                         │
│                   │  (Port 8000)    │                         │
│                   └────────┬────────┘                         │
│                            │                                  │
│    ┌───────────────────────┼───────────────────────┐         │
│    │                       │                       │         │
│    ▼                       ▼                       ▼         │
│ ┌────────┐          ┌──────────┐          ┌──────────┐      │
│ │Dashboard│          │  Models  │          │ Triggers │      │
│ │ Service │          │ Service  │          │ Service  │      │
│ └────────┘          └──────────┘          └──────────┘      │
│    │                       │                       │         │
│    ▼                       ▼                       ▼         │
│ ┌────────┐          ┌──────────┐          ┌──────────┐      │
│ │ Climate│          │   Risk   │          │   Auth   │      │
│ │ Service│          │ Service  │          │ Service  │      │
│ └────────┘          └──────────┘          └──────────┘      │
└────────────────────────────┬──────────────────────────────────┘
                             │
                             │ REST API
                             │
┌────────────────────────────┼──────────────────────────────────┐
│                     Frontend Layer                            │
│                   ┌────────┴────────┐                         │
│                   │   React App     │                         │
│                   │  (Port 3000)    │                         │
│                   └────────┬────────┘                         │
│                            │                                  │
│    ┌───────────────────────┼───────────────────────┐         │
│    │                       │                       │         │
│    ▼                       ▼                       ▼         │
│ ┌────────┐          ┌──────────┐          ┌──────────┐      │
│ │Executive│          │  Models  │          │ Triggers │      │
│ │Dashboard│          │Dashboard │          │Dashboard │      │
│ └────────┘          └──────────┘          └──────────┘      │
│    │                       │                       │         │
│    ▼                       ▼                       ▼         │
│ ┌────────┐          ┌──────────┐          ┌──────────┐      │
│ │ Climate│          │   Risk   │          │   Auth   │      │
│ │Dashboard│          │Dashboard │          │  Pages   │      │
│ └────────┘          └──────────┘          └──────────┘      │
└───────────────────────────────────────────────────────────────┘
```

### Data Flow

```
CSV Files → Data Loaders → PostgreSQL → Backend API → Frontend Dashboard
    ↓
outputs/processed/
├── master_dataset.csv
├── chirps_processed.csv
├── ndvi_processed.csv
└── training_results.json
```

## Components and Interfaces

### 1. Data Loading Scripts

#### Climate Data Loader (`backend/load_climate_data.py`)

**Purpose:** Load master_dataset.csv into climate_data table

**Interface:**
```python
def load_climate_data(
    csv_path: str,
    db_url: str,
    clear_existing: bool = False
) -> Dict[str, Any]:
    """
    Load climate data from CSV into database.
    
    Args:
        csv_path: Path to master_dataset.csv
        db_url: PostgreSQL connection string
        clear_existing: Whether to truncate table before loading
        
    Returns:
        Dict with status, records_loaded, errors
    """
```

**Key Functions:**
- `read_csv_data()` - Read and validate CSV
- `transform_data()` - Convert data types, handle nulls
- `insert_records()` - Bulk insert with transaction
- `verify_load()` - Count records and validate

#### Trigger Events Loader (`backend/load_trigger_events.py`)

**Purpose:** Extract and load trigger events from processed CSVs

**Interface:**
```python
def load_trigger_events(
    chirps_path: str,
    ndvi_path: str,
    db_url: str
) -> Dict[str, Any]:
    """
    Load trigger events from processed data.
    
    Args:
        chirps_path: Path to chirps_processed.csv
        ndvi_path: Path to ndvi_processed.csv
        db_url: PostgreSQL connection string
        
    Returns:
        Dict with counts by trigger type
    """
```

**Key Functions:**
- `extract_drought_triggers()` - Parse drought events
- `extract_flood_triggers()` - Parse flood events
- `extract_crop_failure_triggers()` - Parse crop failure events
- `insert_trigger_events()` - Bulk insert triggers

#### Model Metrics Loader (`backend/load_model_metrics.py`)

**Purpose:** Load ML model training results into database

**Interface:**
```python
def load_model_metrics(
    results_path: str,
    feature_importance_dir: str,
    db_url: str
) -> Dict[str, Any]:
    """
    Load model metrics and feature importance.
    
    Args:
        results_path: Path to training_results.json
        feature_importance_dir: Directory with feature importance CSVs
        db_url: PostgreSQL connection string
        
    Returns:
        Dict with models loaded and status
    """
```

**Key Functions:**
- `parse_training_results()` - Extract metrics from JSON
- `load_feature_importance()` - Read feature importance CSVs
- `insert_model_metrics()` - Insert model records
- `insert_feature_importance()` - Insert top features

### 2. Database Schema

#### climate_data Table

```sql
CREATE TABLE climate_data (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    
    -- Weather data
    temp_mean_c FLOAT,
    temp_max_c FLOAT,
    temp_min_c FLOAT,
    rainfall_mm FLOAT,
    humidity_pct FLOAT,
    
    -- Vegetation
    ndvi FLOAT,
    vci FLOAT,
    
    -- Climate indices
    oni FLOAT,
    iod FLOAT,
    enso_phase VARCHAR(50),
    
    -- Triggers
    drought_trigger BOOLEAN,
    flood_trigger BOOLEAN,
    crop_failure_trigger BOOLEAN,
    
    -- Risk scores
    drought_risk_score FLOAT,
    flood_risk_score FLOAT,
    overall_climate_risk FLOAT,
    
    -- Metadata
    data_quality VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(year, month)
);

CREATE INDEX idx_climate_date ON climate_data(year, month);
CREATE INDEX idx_climate_triggers ON climate_data(drought_trigger, flood_trigger, crop_failure_trigger);
```

#### trigger_events Table

```sql
CREATE TABLE trigger_events (
    id SERIAL PRIMARY KEY,
    event_date DATE NOT NULL,
    event_type VARCHAR(50) NOT NULL,  -- 'drought', 'flood', 'crop_failure'
    severity VARCHAR(20),              -- 'low', 'moderate', 'high', 'critical'
    confidence FLOAT,
    
    -- Event details
    location VARCHAR(100),
    latitude FLOAT,
    longitude FLOAT,
    
    -- Metrics
    rainfall_deficit_mm FLOAT,
    rainfall_excess_mm FLOAT,
    ndvi_value FLOAT,
    vci_value FLOAT,
    
    -- Metadata
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_trigger_date ON trigger_events(event_date);
CREATE INDEX idx_trigger_type ON trigger_events(event_type);
CREATE INDEX idx_trigger_severity ON trigger_events(severity);
```

#### model_metrics Table

```sql
CREATE TABLE model_metrics (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,  -- 'random_forest', 'xgboost', 'lstm', 'ensemble'
    
    -- Performance metrics
    r2_score FLOAT,
    rmse FLOAT,
    mae FLOAT,
    mape FLOAT,
    
    -- Training info
    training_samples INTEGER,
    validation_samples INTEGER,
    test_samples INTEGER,
    training_time_seconds FLOAT,
    
    -- Metadata
    training_date TIMESTAMP,
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_model_name ON model_metrics(model_name);
CREATE INDEX idx_model_type ON model_metrics(model_type);
```

#### feature_importance Table

```sql
CREATE TABLE feature_importance (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES model_metrics(id),
    feature_name VARCHAR(200) NOT NULL,
    importance_score FLOAT NOT NULL,
    rank INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_feature_model ON feature_importance(model_id);
CREATE INDEX idx_feature_rank ON feature_importance(rank);
```

### 3. Backend API Enhancements

#### Data Endpoints (Already Implemented)

The backend already has these endpoints implemented:

**Dashboard Endpoints:**
- `GET /api/dashboard/kpis` - Executive KPIs
- `GET /api/dashboard/trends` - 12-month trends
- `GET /api/dashboard/sustainability` - Sustainability status

**Model Endpoints:**
- `GET /api/models/metrics` - All model metrics
- `GET /api/models/compare` - Compare models
- `GET /api/models/{model_id}/feature-importance` - Feature importance

**Trigger Endpoints:**
- `GET /api/triggers/events` - Historical triggers
- `GET /api/triggers/timeline` - Timeline data
- `GET /api/triggers/forecast` - Forecasts

**Climate Endpoints:**
- `GET /api/climate/timeseries` - Time series data
- `GET /api/climate/anomalies` - Anomaly detection
- `GET /api/climate/correlations` - Correlation matrix

**Risk Endpoints:**
- `GET /api/risk/portfolio` - Portfolio metrics
- `POST /api/risk/scenario` - Scenario analysis

### 4. Frontend Dashboard Pages

#### Executive Dashboard (`frontend/src/pages/ExecutiveDashboard.jsx`)

**Components:**
- KPI Cards (trigger rates, sustainability)
- Trend Charts (rainfall, NDVI, temperature)
- Risk Summary
- Recent Alerts

**Data Sources:**
- `/api/dashboard/kpis`
- `/api/dashboard/trends`
- `/api/triggers/events?limit=5`

#### Model Performance Dashboard (`frontend/src/pages/ModelsDashboard.jsx`)

**Components:**
- Model Comparison Table
- Performance Charts (R², RMSE, MAE)
- Feature Importance Charts
- Prediction vs Actual Scatter Plots

**Data Sources:**
- `/api/models/metrics`
- `/api/models/compare`
- `/api/models/{id}/feature-importance`

#### Triggers Dashboard (`frontend/src/pages/TriggersDashboard.jsx`)

**Components:**
- Timeline Visualization
- Filter Controls (type, date, severity)
- Trigger Details Table
- Export Button

**Data Sources:**
- `/api/triggers/events`
- `/api/triggers/timeline`
- `/api/triggers/export`

#### Climate Insights Dashboard (`frontend/src/pages/ClimateDashboard.jsx`)

**Components:**
- Time Series Charts (rainfall, temp, NDVI)
- Anomaly Highlights
- Correlation Matrix Heatmap
- Seasonal Pattern Overlay

**Data Sources:**
- `/api/climate/timeseries`
- `/api/climate/anomalies`
- `/api/climate/correlations`

#### Risk Management Dashboard (`frontend/src/pages/RiskDashboard.jsx`)

**Components:**
- Portfolio Metrics Cards
- Trigger Distribution Pie Chart
- Scenario Analysis Results
- Early Warning Alerts

**Data Sources:**
- `/api/risk/portfolio`
- `/api/risk/scenario`
- `/api/triggers/alerts`

### 5. Docker Compose Configuration

#### Service Definitions

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: climate_db
      POSTGRES_USER: climate_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U climate_user"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://climate_user:${DB_PASSWORD}@postgres:5432/climate_db
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - ../outputs:/outputs
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm start

volumes:
  postgres_data:
```

## Data Models

### Climate Data Model

```python
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ClimateData(Base):
    __tablename__ = 'climate_data'
    
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    # Weather
    temp_mean_c = Column(Float)
    temp_max_c = Column(Float)
    temp_min_c = Column(Float)
    rainfall_mm = Column(Float)
    humidity_pct = Column(Float)
    
    # Vegetation
    ndvi = Column(Float)
    vci = Column(Float)
    
    # Climate indices
    oni = Column(Float)
    iod = Column(Float)
    enso_phase = Column(String(50))
    
    # Triggers
    drought_trigger = Column(Boolean)
    flood_trigger = Column(Boolean)
    crop_failure_trigger = Column(Boolean)
    
    # Risk scores
    drought_risk_score = Column(Float)
    flood_risk_score = Column(Float)
    overall_climate_risk = Column(Float)
    
    # Metadata
    data_quality = Column(String(20))
    created_at = Column(DateTime)
```

### Trigger Event Model

```python
class TriggerEvent(Base):
    __tablename__ = 'trigger_events'
    
    id = Column(Integer, primary_key=True)
    event_date = Column(Date, nullable=False)
    event_type = Column(String(50), nullable=False)
    severity = Column(String(20))
    confidence = Column(Float)
    
    # Location
    location = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Metrics
    rainfall_deficit_mm = Column(Float)
    rainfall_excess_mm = Column(Float)
    ndvi_value = Column(Float)
    vci_value = Column(Float)
    
    # Metadata
    metadata = Column(JSON)
    created_at = Column(DateTime)
```

### Model Metrics Model

```python
class ModelMetrics(Base):
    __tablename__ = 'model_metrics'
    
    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)
    
    # Performance
    r2_score = Column(Float)
    rmse = Column(Float)
    mae = Column(Float)
    mape = Column(Float)
    
    # Training info
    training_samples = Column(Integer)
    validation_samples = Column(Integer)
    test_samples = Column(Integer)
    training_time_seconds = Column(Float)
    
    # Metadata
    training_date = Column(DateTime)
    model_version = Column(String(50))
    created_at = Column(DateTime)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Data Loading Completeness
*For any* CSV file loaded, the number of records in the database should equal the number of data rows in the CSV file (excluding header).

**Validates: Requirements 1.2, 1.3**

### Property 2: Trigger Event Consistency
*For any* month in the climate_data table where a trigger flag is true, there should exist a corresponding record in the trigger_events table with matching date and type.

**Validates: Requirements 2.4, 2.5**

### Property 3: Model Metrics Completeness
*For any* model type in the training results, there should exist exactly one record in the model_metrics table with all required metrics (R², RMSE, MAE, MAPE) populated.

**Validates: Requirements 3.3, 3.5**

### Property 4: API Response Validity
*For any* valid API endpoint request, the response should return HTTP 200 status and valid JSON data matching the expected schema.

**Validates: Requirements 4.2, 4.3**

### Property 5: Dashboard Data Consistency
*For any* dashboard page load, the displayed data should match the data returned by the corresponding API endpoint within the last refresh interval.

**Validates: Requirements 6.1, 6.5**

### Property 6: Date Range Integrity
*For any* query with date filters, the returned records should have dates within the specified range (2018-2023).

**Validates: Requirements 13.3**

### Property 7: Null Handling Safety
*For any* null value in the database, the frontend should display "N/A" or skip the data point without throwing errors.

**Validates: Requirements 14.1, 14.4**

### Property 8: Service Health Verification
*For any* health check request, if the database is accessible, the response should return "healthy" status within 1 second.

**Validates: Requirements 15.1, 15.2**

### Property 9: Authentication Token Validity
*For any* authenticated API request, the JWT token should be valid and not expired, or the request should return HTTP 401.

**Validates: Requirements 4.5**

### Property 10: Data Refresh Idempotence
*For any* data refresh operation, performing the refresh multiple times should result in the same data state as performing it once.

**Validates: Requirements 17.1, 17.3**

## Error Handling

### Data Loading Errors

**Error Types:**
1. **File Not Found** - CSV file doesn't exist
2. **Invalid Data Format** - CSV has wrong structure
3. **Database Connection Failed** - Cannot connect to PostgreSQL
4. **Duplicate Records** - Records already exist
5. **Validation Failed** - Data doesn't meet constraints

**Handling Strategy:**
```python
try:
    # Load data
    records = load_climate_data(csv_path, db_url)
except FileNotFoundError as e:
    logger.error(f"CSV file not found: {e}")
    return {"status": "error", "message": "File not found", "file": csv_path}
except ValidationError as e:
    logger.error(f"Data validation failed: {e}")
    db.rollback()
    return {"status": "error", "message": "Invalid data", "details": str(e)}
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    db.rollback()
    return {"status": "error", "message": "Database error", "details": str(e)}
```

### API Errors

**Error Responses:**
```json
{
  "error": {
    "code": "DATA_NOT_FOUND",
    "message": "No climate data found for specified date range",
    "details": {
      "start_date": "2024-01-01",
      "end_date": "2024-12-31"
    }
  }
}
```

**HTTP Status Codes:**
- 400 - Bad Request (invalid parameters)
- 401 - Unauthorized (missing/invalid token)
- 404 - Not Found (resource doesn't exist)
- 500 - Internal Server Error (unexpected error)

### Frontend Errors

**Error Display:**
```jsx
{error && (
  <Alert severity="error">
    <AlertTitle>Error Loading Data</AlertTitle>
    {error.message}
    <Button onClick={handleRetry}>Retry</Button>
  </Alert>
)}
```

**Fallback Behavior:**
- Display cached data if available
- Show "No data available" message
- Provide retry button
- Log error to console

## Testing Strategy

### Unit Tests

**Data Loaders:**
```python
def test_load_climate_data_success():
    """Test successful climate data loading"""
    result = load_climate_data(test_csv_path, test_db_url)
    assert result['status'] == 'success'
    assert result['records_loaded'] == 72

def test_load_climate_data_duplicate():
    """Test handling of duplicate records"""
    load_climate_data(test_csv_path, test_db_url)
    result = load_climate_data(test_csv_path, test_db_url)
    assert result['status'] == 'error'
    assert 'duplicate' in result['message'].lower()
```

**API Endpoints:**
```python
def test_get_dashboard_kpis():
    """Test dashboard KPIs endpoint"""
    response = client.get("/api/dashboard/kpis")
    assert response.status_code == 200
    data = response.json()
    assert 'drought_rate' in data
    assert 'flood_rate' in data
    assert 'crop_failure_rate' in data
```

### Integration Tests

**End-to-End Data Flow:**
```python
def test_data_loading_to_dashboard():
    """Test complete data flow from CSV to dashboard"""
    # 1. Load data
    load_result = load_climate_data(csv_path, db_url)
    assert load_result['status'] == 'success'
    
    # 2. Query API
    response = client.get("/api/climate/timeseries?variable=rainfall_mm")
    assert response.status_code == 200
    
    # 3. Verify data
    data = response.json()
    assert len(data) == 72
    assert data[0]['year'] == 2018
```

### Property-Based Tests

**Property 1: Data Loading Completeness**
```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=1, max_value=1000))
def test_data_loading_completeness(num_records):
    """Property: Loaded records should equal CSV rows"""
    # Generate test CSV with num_records rows
    test_csv = generate_test_csv(num_records)
    
    # Load data
    result = load_climate_data(test_csv, test_db_url, clear_existing=True)
    
    # Verify
    db_count = count_records(test_db_url)
    assert db_count == num_records
```

**Property 2: Trigger Event Consistency**
```python
@given(st.lists(st.booleans(), min_size=72, max_size=72))
def test_trigger_consistency(trigger_flags):
    """Property: Trigger flags should match trigger events"""
    # Create climate data with trigger flags
    create_test_climate_data(trigger_flags)
    
    # Load trigger events
    load_trigger_events(chirps_path, ndvi_path, test_db_url)
    
    # Verify consistency
    for i, flag in enumerate(trigger_flags):
        if flag:
            assert trigger_event_exists(year=2018, month=i+1)
```

## Deployment

### Development Environment

**Setup Steps:**
1. Clone repository
2. Copy `.env.template` to `.env`
3. Set environment variables
4. Run `docker-compose up`
5. Run data loading scripts
6. Access dashboard at http://localhost:3000

**Environment Variables:**
```bash
# Database
DB_PASSWORD=your_secure_password
DATABASE_URL=postgresql://climate_user:${DB_PASSWORD}@localhost:5432/climate_db

# Backend
SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

### Production Environment

**Additional Steps:**
1. Use production database (managed PostgreSQL)
2. Enable HTTPS with SSL certificates
3. Set up reverse proxy (Nginx)
4. Configure monitoring (Prometheus/Grafana)
5. Set up automated backups
6. Enable log aggregation

**Production Environment Variables:**
```bash
# Database
DATABASE_URL=postgresql://user:pass@prod-db.example.com:5432/climate_db

# Backend
SECRET_KEY=<strong-random-key>
ENVIRONMENT=production
DEBUG=false

# Frontend
REACT_APP_API_URL=https://api.climate-prediction.example.com
```

### Monitoring

**Health Checks:**
- Database connectivity check every 30 seconds
- API endpoint availability check every minute
- Frontend accessibility check every minute

**Metrics to Track:**
- API response times
- Database query performance
- Error rates
- Active user sessions
- Data refresh frequency

**Alerting:**
- Alert if database connection fails
- Alert if API response time > 2 seconds
- Alert if error rate > 5%
- Alert if disk space < 10%

## Security Considerations

### Authentication
- JWT tokens with 30-minute expiration
- Bcrypt password hashing (12 rounds)
- Role-based access control (admin, analyst, viewer)

### Data Protection
- Database credentials in environment variables
- HTTPS for all API communication
- SQL injection prevention (parameterized queries)
- Input validation on all endpoints

### Access Control
- Admin: Full access to all features
- Analyst: Read/write access to data
- Viewer: Read-only access

## Performance Optimization

### Database
- Indexes on frequently queried columns (year, month, trigger flags)
- Connection pooling (20 connections)
- Query result caching (5-minute TTL)

### API
- Response compression (gzip)
- Pagination for large result sets
- Async endpoints for long-running operations

### Frontend
- Code splitting for faster initial load
- Lazy loading of dashboard pages
- Chart data sampling for large datasets
- Debounced search and filter inputs

## Maintenance

### Data Updates
- Run data loading scripts when new data is available
- Verify data integrity after each load
- Monitor for data quality issues

### Database Maintenance
- Weekly vacuum and analyze
- Monthly backup verification
- Quarterly index optimization

### Monitoring
- Daily health check review
- Weekly performance analysis
- Monthly capacity planning

---

**Design Version:** 1.0  
**Last Updated:** November 21, 2025  
**Status:** Ready for Implementation
