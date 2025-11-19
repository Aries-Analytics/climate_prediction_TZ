# Design Document: Interactive Dashboard System

## Overview

This design establishes a modern, scalable web application for the Tanzania Climate Prediction platform. The system uses a decoupled architecture with FastAPI backend, React frontend, and PostgreSQL database to deliver interactive dashboards for climate insights, ML model monitoring, insurance triggers, and risk management.

The application serves multiple stakeholder types (executives, data scientists, insurance analysts, risk managers) with role-based access control and real-time data visualization capabilities.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  React Frontend (Port 3000)                                      │
│  ├── Dashboard Components (Executive, Models, Triggers, etc.)   │
│  ├── Visualization Library (Plotly.js)                          │
│  ├── State Management (React Context/Redux)                     │
│  └── API Client (Axios)                                         │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS/REST
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Backend (Port 8000)                                     │
│  ├── Authentication & Authorization (JWT)                       │
│  ├── API Endpoints (RESTful)                                    │
│  ├── Business Logic Services                                    │
│  ├── Data Access Layer (SQLAlchemy ORM)                        │
│  └── Background Tasks (Celery - optional)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │ SQL
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATABASE LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL (Port 5432)                                          │
│  ├── Users & Authentication                                     │
│  ├── Climate Data & Predictions                                 │
│  ├── Trigger Events & Alerts                                    │
│  ├── Model Metrics & Experiments                                │
│  └── Audit Logs                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FILE STORAGE LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  ├── outputs/processed/ (CSV/Parquet datasets)                  │
│  ├── outputs/models/ (Trained ML models)                        │
│  ├── outputs/evaluation/ (Charts, reports)                      │
│  └── outputs/business_reports/ (Business metrics)               │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- **Framework:** FastAPI 0.104+ (Python 3.9+)
- **ORM:** SQLAlchemy 2.0+
- **Database:** PostgreSQL 15+
- **Authentication:** JWT (python-jose)
- **Password Hashing:** bcrypt
- **Validation:** Pydantic v2
- **API Documentation:** OpenAPI/Swagger (built-in)

**Frontend:**
- **Framework:** React 18+
- **Build Tool:** Vite
- **UI Library:** Material-UI (MUI) v5
- **Charts:** Plotly.js / Recharts
- **HTTP Client:** Axios
- **State Management:** React Context API (or Redux if needed)
- **Routing:** React Router v6

**Database:**
- **Primary:** PostgreSQL 15+
- **Connection Pool:** psycopg2 / asyncpg
- **Migrations:** Alembic

**Deployment:**
- **Containerization:** Docker + Docker Compose
- **Web Server:** Nginx (reverse proxy)
- **HTTPS:** Let's Encrypt / SSL certificates
- **Cloud:** AWS/Azure/GCP (or self-hosted)

## Components and Interfaces

### Backend Components

#### 1. Authentication Service

**Module:** `backend/app/services/auth_service.py`

**Responsibilities:**
- User registration and login
- JWT token generation and validation
- Password hashing and verification
- Session management

**Key Functions:**
```python
def create_user(username: str, email: str, password: str, role: str) -> User
def authenticate_user(username: str, password: str) -> Optional[User]
def create_access_token(user_id: int) -> str
def verify_token(token: str) -> Optional[int]
def hash_password(password: str) -> str
def verify_password(plain_password: str, hashed_password: str) -> bool
```

#### 2. Dashboard Data Service

**Module:** `backend/app/services/dashboard_service.py`

**Responsibilities:**
- Aggregate KPIs for executive dashboard
- Calculate trigger rates and loss ratios
- Generate trend data for charts
- Compute sustainability metrics

**Key Functions:**
```python
def get_executive_kpis() -> ExecutiveKPIs
def get_trigger_rates(start_date: date, end_date: date) -> TriggerRates
def get_loss_ratio_trend(months: int) -> List[LossRatioPoint]
def get_sustainability_status() -> SustainabilityStatus
```

#### 3. Model Performance Service

**Module:** `backend/app/services/model_service.py`

**Responsibilities:**
- Load model evaluation metrics
- Compare model performance
- Track model drift
- Generate retraining recommendations

**Key Functions:**
```python
def get_model_metrics(model_name: str) -> ModelMetrics
def compare_models(model_names: List[str]) -> ModelComparison
def get_feature_importance(model_name: str) -> List[FeatureImportance]
def check_model_drift(model_name: str) -> DriftStatus
def get_prediction_history(model_name: str, limit: int) -> List[Prediction]
```

#### 4. Trigger Events Service

**Module:** `backend/app/services/trigger_service.py`

**Responsibilities:**
- Query historical trigger events
- Calculate trigger probabilities from ML predictions
- Generate early warning alerts
- Export trigger data

**Key Functions:**
```python
def get_trigger_events(start_date: date, end_date: date, event_type: str) -> List[TriggerEvent]
def get_trigger_timeline() -> List[TimelineEvent]
def forecast_trigger_probabilities(months_ahead: int) -> List[TriggerForecast]
def generate_early_warnings() -> List[EarlyWarning]
def export_triggers_csv(filters: TriggerFilters) -> bytes
```

#### 5. Climate Insights Service

**Module:** `backend/app/services/climate_service.py`

**Responsibilities:**
- Load climate time series data
- Calculate anomalies and trends
- Compute correlations
- Identify seasonal patterns

**Key Functions:**
```python
def get_climate_timeseries(variable: str, start_date: date, end_date: date) -> TimeSeries
def calculate_anomalies(variable: str) -> List[Anomaly]
def get_correlation_matrix(variables: List[str]) -> CorrelationMatrix
def get_seasonal_patterns(variable: str) -> SeasonalPattern
```

#### 6. Risk Management Service

**Module:** `backend/app/services/risk_service.py`

**Responsibilities:**
- Calculate portfolio-level metrics
- Run scenario analysis
- Generate risk reports
- Provide recommendations

**Key Functions:**
```python
def get_portfolio_metrics() -> PortfolioMetrics
def run_scenario_analysis(scenario: Scenario) -> ScenarioResult
def generate_risk_report(format: str) -> bytes
def get_recommendations() -> List[Recommendation]
```

### API Endpoints

#### Authentication Endpoints

```
POST   /api/auth/register          # Register new user
POST   /api/auth/login             # Login and get JWT token
POST   /api/auth/logout            # Logout (invalidate token)
GET    /api/auth/me                # Get current user info
PUT    /api/auth/change-password   # Change password
```

#### Dashboard Endpoints

```
GET    /api/dashboard/executive    # Executive KPIs
GET    /api/dashboard/triggers     # Trigger rates and trends
GET    /api/dashboard/sustainability # Sustainability metrics
```

#### Model Endpoints

```
GET    /api/models                 # List all models
GET    /api/models/{name}          # Get model details
GET    /api/models/{name}/metrics  # Get model metrics
GET    /api/models/{name}/importance # Get feature importance
GET    /api/models/compare         # Compare multiple models
POST   /api/models/{name}/retrain  # Trigger model retraining
```

#### Trigger Endpoints

```
GET    /api/triggers               # List trigger events (paginated)
GET    /api/triggers/timeline      # Get timeline view
GET    /api/triggers/forecast      # Get trigger probability forecasts
GET    /api/triggers/export        # Export triggers as CSV
POST   /api/triggers/alerts        # Create manual alert
```

#### Climate Endpoints

```
GET    /api/climate/timeseries     # Get time series data
GET    /api/climate/anomalies      # Get detected anomalies
GET    /api/climate/correlations   # Get correlation matrix
GET    /api/climate/seasonal       # Get seasonal patterns
```

#### Risk Endpoints

```
GET    /api/risk/portfolio         # Portfolio metrics
POST   /api/risk/scenario          # Run scenario analysis
GET    /api/risk/report            # Generate risk report
GET    /api/risk/recommendations   # Get recommendations
```

#### Admin Endpoints

```
GET    /api/admin/users            # List all users
POST   /api/admin/users            # Create user
PUT    /api/admin/users/{id}       # Update user
DELETE /api/admin/users/{id}       # Delete user
GET    /api/admin/audit-logs       # Get audit logs
GET    /api/admin/health           # System health check
```

### Frontend Components

#### 1. Layout Components

**AppLayout** (`src/components/layout/AppLayout.tsx`)
- Top navigation bar
- Sidebar menu
- Main content area
- Footer

**Sidebar** (`src/components/layout/Sidebar.tsx`)
- Dashboard navigation links
- User profile section
- Logout button

#### 2. Dashboard Components

**ExecutiveDashboard** (`src/pages/ExecutiveDashboard.tsx`)
- KPI cards (trigger rates, loss ratio, sustainability)
- Trend charts (12-month view)
- Alert indicators
- Quick actions

**ModelPerformanceDashboard** (`src/pages/ModelPerformanceDashboard.tsx`)
- Model comparison table
- Performance metrics charts
- Feature importance visualization
- Drift monitoring alerts

**TriggersDashboard** (`src/pages/TriggersDashboard.tsx`)
- Interactive timeline
- Trigger event table (filterable)
- Forecast probability charts
- Export functionality

**ClimateInsightsDashboard** (`src/pages/ClimateInsightsDashboard.tsx`)
- Multi-variable time series charts
- Anomaly highlights
- Correlation heatmap
- Seasonal pattern overlays

**RiskManagementDashboard** (`src/pages/RiskManagementDashboard.tsx`)
- Portfolio summary cards
- Scenario analysis interface
- Early warning alerts
- Recommendation list

#### 3. Reusable UI Components

**KPICard** (`src/components/common/KPICard.tsx`)
- Display metric value
- Show trend indicator (up/down)
- Color coding (green/yellow/red)
- Tooltip with details

**Chart** (`src/components/charts/Chart.tsx`)
- Wrapper for Plotly.js
- Consistent styling
- Responsive sizing
- Export functionality

**DataTable** (`src/components/common/DataTable.tsx`)
- Sortable columns
- Filterable rows
- Pagination
- Export to CSV

**LoadingSpinner** (`src/components/common/LoadingSpinner.tsx`)
- Consistent loading indicator

**ErrorBoundary** (`src/components/common/ErrorBoundary.tsx`)
- Catch and display errors gracefully

#### 4. Authentication Components

**LoginPage** (`src/pages/LoginPage.tsx`)
- Username/password form
- Remember me checkbox
- Error messages

**ProtectedRoute** (`src/components/auth/ProtectedRoute.tsx`)
- Check authentication
- Redirect to login if needed
- Role-based access control

## Data Models

### Database Schema

#### Users Table

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'analyst', 'viewer')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

#### Climate Data Table

```sql
CREATE TABLE climate_data (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    location_lat DECIMAL(10, 6),
    location_lon DECIMAL(10, 6),
    temperature_avg DECIMAL(5, 2),
    rainfall_mm DECIMAL(7, 2),
    ndvi DECIMAL(4, 3),
    enso_index DECIMAL(5, 3),
    iod_index DECIMAL(5, 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_climate_date ON climate_data(date);
CREATE INDEX idx_climate_location ON climate_data(location_lat, location_lon);
```

#### Trigger Events Table

```sql
CREATE TABLE trigger_events (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    trigger_type VARCHAR(50) NOT NULL CHECK (trigger_type IN ('drought', 'flood', 'crop_failure')),
    confidence DECIMAL(4, 3) CHECK (confidence BETWEEN 0 AND 1),
    severity DECIMAL(4, 3) CHECK (severity BETWEEN 0 AND 1),
    payout_amount DECIMAL(10, 2),
    location_lat DECIMAL(10, 6),
    location_lon DECIMAL(10, 6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trigger_date ON trigger_events(date);
CREATE INDEX idx_trigger_type ON trigger_events(trigger_type);
```

#### Model Predictions Table

```sql
CREATE TABLE model_predictions (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(50) NOT NULL,
    prediction_date DATE NOT NULL,
    target_date DATE NOT NULL,
    predicted_value DECIMAL(10, 4),
    actual_value DECIMAL(10, 4),
    confidence_lower DECIMAL(10, 4),
    confidence_upper DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_predictions_model ON model_predictions(model_name);
CREATE INDEX idx_predictions_target_date ON model_predictions(target_date);
```

#### Model Metrics Table

```sql
CREATE TABLE model_metrics (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(50) NOT NULL,
    experiment_id VARCHAR(100),
    r2_score DECIMAL(6, 4),
    rmse DECIMAL(10, 4),
    mae DECIMAL(10, 4),
    mape DECIMAL(6, 4),
    training_date TIMESTAMP NOT NULL,
    data_start_date DATE,
    data_end_date DATE,
    hyperparameters JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_model ON model_metrics(model_name);
CREATE INDEX idx_metrics_training_date ON model_metrics(training_date);
```

#### Audit Logs Table

```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    details JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_created ON audit_logs(created_at);
```

### Pydantic Models (Backend)

#### User Models

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
```

#### Dashboard Models

```python
from pydantic import BaseModel
from typing import List
from datetime import date

class TriggerRate(BaseModel):
    trigger_type: str
    rate: float
    count: int
    target_min: float
    target_max: float
    status: str  # "within_target", "below_target", "above_target"

class ExecutiveKPIs(BaseModel):
    flood_trigger_rate: TriggerRate
    drought_trigger_rate: TriggerRate
    crop_failure_trigger_rate: TriggerRate
    combined_trigger_rate: float
    loss_ratio: float
    sustainability_status: str  # "sustainable", "warning", "unsustainable"
    total_triggers_ytd: int
    estimated_payouts_ytd: float

class TrendPoint(BaseModel):
    date: date
    value: float

class LossRatioTrend(BaseModel):
    data: List[TrendPoint]
    target_threshold: float
```

#### Model Performance Models

```python
from pydantic import BaseModel
from typing import List, Dict

class ModelMetrics(BaseModel):
    model_name: str
    r2_score: float
    rmse: float
    mae: float
    mape: float
    training_date: datetime
    experiment_id: str

class FeatureImportance(BaseModel):
    feature_name: str
    importance: float
    rank: int

class ModelComparison(BaseModel):
    models: List[ModelMetrics]
    best_model: str
    comparison_metric: str  # "r2_score", "rmse", etc.

class DriftStatus(BaseModel):
    model_name: str
    is_drifting: bool
    drift_score: float
    threshold: float
    recommendation: str
```

#### Trigger Models

```python
from pydantic import BaseModel
from datetime import date
from typing import Optional

class TriggerEvent(BaseModel):
    id: int
    date: date
    trigger_type: str
    confidence: float
    severity: float
    payout_amount: float
    location_lat: Optional[float]
    location_lon: Optional[float]

class TriggerForecast(BaseModel):
    target_date: date
    trigger_type: str
    probability: float
    confidence_lower: float
    confidence_upper: float

class EarlyWarning(BaseModel):
    alert_type: str
    severity: str  # "low", "medium", "high"
    message: str
    trigger_probability: float
    target_date: date
    recommended_action: str
```

### TypeScript Interfaces (Frontend)

```typescript
// User interfaces
export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'analyst' | 'viewer';
  isActive: boolean;
  createdAt: string;
  lastLogin?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthToken {
  accessToken: string;
  tokenType: string;
}

// Dashboard interfaces
export interface TriggerRate {
  triggerType: string;
  rate: number;
  count: number;
  targetMin: number;
  targetMax: number;
  status: 'within_target' | 'below_target' | 'above_target';
}

export interface ExecutiveKPIs {
  floodTriggerRate: TriggerRate;
  droughtTriggerRate: TriggerRate;
  cropFailureTriggerRate: TriggerRate;
  combinedTriggerRate: number;
  lossRatio: number;
  sustainabilityStatus: 'sustainable' | 'warning' | 'unsustainable';
  totalTriggersYtd: number;
  estimatedPayoutsYtd: number;
}

// Model interfaces
export interface ModelMetrics {
  modelName: string;
  r2Score: number;
  rmse: number;
  mae: number;
  mape: number;
  trainingDate: string;
  experimentId: string;
}

export interface FeatureImportance {
  featureName: string;
  importance: number;
  rank: number;
}

// Chart data interfaces
export interface TimeSeriesPoint {
  date: string;
  value: number;
}

export interface ChartData {
  x: (string | number)[];
  y: (string | number)[];
  type: 'scatter' | 'bar' | 'line';
  name?: string;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Authentication token validity

*For any* valid user credentials, when authentication succeeds, the generated JWT token should be verifiable and contain the correct user ID

**Validates: Requirements 1.2, 1.3**

### Property 2: Role-based access control

*For any* authenticated user with role R, when accessing endpoint E, access should be granted if and only if role R has permission for endpoint E

**Validates: Requirements 1.5**

### Property 3: Dashboard data consistency

*For any* time period T, the sum of individual trigger events in period T should equal the total trigger count displayed for period T

**Validates: Requirements 2.2, 4.1**

### Property 4: Loss ratio calculation accuracy

*For any* set of trigger events and premium data, the calculated loss ratio should equal total_payouts ÷ total_premiums

**Validates: Requirements 2.2, 6.2**

### Property 5: Model comparison consistency

*For any* set of models M, when comparing by metric X, the ranking should be consistent with the actual metric values in descending order

**Validates: Requirements 3.3**

### Property 6: Trigger forecast temporal ordering

*For any* trigger forecast, the target_date should be greater than the prediction_date

**Validates: Requirements 4.3, 16.1**

### Property 7: API response format consistency

*For any* successful API request, the response should be valid JSON with appropriate HTTP status code (200-299)

**Validates: Requirements 7.2**

### Property 8: Error response structure

*For any* failed API request, the response should contain an error message, error code, and appropriate HTTP status code (400-599)

**Validates: Requirements 7.3, 9.1**

### Property 9: Data export completeness

*For any* data export request with filters F, the exported data should contain all and only records matching filters F

**Validates: Requirements 4.5, 18.2**

### Property 10: Pagination correctness

*For any* paginated API endpoint with page P and size S, the response should contain exactly S items (or fewer on the last page) starting at offset P×S

**Validates: Requirements 4.1**

## Error Handling

### Backend Error Handling

**Authentication Errors:**
- **401 Unauthorized**: Invalid credentials, expired token
- **403 Forbidden**: Insufficient permissions for resource
- **Response**: `{"detail": "Could not validate credentials", "error_code": "AUTH_001"}`

**Validation Errors:**
- **422 Unprocessable Entity**: Invalid request body or parameters
- **Response**: `{"detail": [{"loc": ["body", "field"], "msg": "error message", "type": "value_error"}]}`

**Resource Errors:**
- **404 Not Found**: Requested resource doesn't exist
- **Response**: `{"detail": "Resource not found", "error_code": "RES_001"}`

**Server Errors:**
- **500 Internal Server Error**: Unexpected server error
- **Response**: `{"detail": "Internal server error", "error_code": "SRV_001"}`
- **Action**: Log full stack trace, notify administrators

**Database Errors:**
- **503 Service Unavailable**: Database connection failed
- **Response**: `{"detail": "Service temporarily unavailable", "error_code": "DB_001"}`
- **Action**: Retry with exponential backoff, log error

### Frontend Error Handling

**Network Errors:**
- Display toast notification: "Network error. Please check your connection."
- Retry automatically with exponential backoff (3 attempts)
- Show retry button if all attempts fail

**API Errors:**
- Parse error response and display user-friendly message
- Log error details to console for debugging
- Redirect to login page for 401 errors

**Component Errors:**
- Use Error Boundary to catch rendering errors
- Display fallback UI with error message
- Provide "Reload" button to recover

**Loading States:**
- Show skeleton loaders for data-heavy components
- Display spinner for quick operations
- Show progress bar for long operations

**Empty States:**
- Display helpful message when no data available
- Provide guidance on next steps
- Show illustration or icon

## Testing Strategy

### Backend Testing

**Unit Tests (pytest):**
- Test individual service functions
- Mock database calls
- Test authentication logic
- Test data transformations
- Target: >80% code coverage

**Integration Tests:**
- Test API endpoints end-to-end
- Use test database
- Test authentication flow
- Test data retrieval and filtering
- Test error responses

**Example Tests:**
```python
def test_authenticate_user_success():
    """Test successful user authentication"""
    user = create_user("testuser", "test@example.com", "password123", "analyst")
    authenticated = authenticate_user("testuser", "password123")
    assert authenticated is not None
    assert authenticated.id == user.id

def test_get_executive_kpis():
    """Test executive KPIs calculation"""
    # Setup test data
    create_trigger_events(...)
    
    # Call service
    kpis = get_executive_kpis()
    
    # Verify
    assert kpis.flood_trigger_rate.rate >= 0
    assert kpis.loss_ratio >= 0
    assert kpis.sustainability_status in ["sustainable", "warning", "unsustainable"]

def test_api_endpoint_requires_auth(client):
    """Test that protected endpoints require authentication"""
    response = client.get("/api/dashboard/executive")
    assert response.status_code == 401
```

### Frontend Testing

**Component Tests (React Testing Library):**
- Test component rendering
- Test user interactions
- Test prop handling
- Mock API calls

**Example Tests:**
```typescript
describe('KPICard', () => {
  it('renders metric value correctly', () => {
    render(<KPICard title="Loss Ratio" value={0.65} status="sustainable" />);
    expect(screen.getByText('0.65')).toBeInTheDocument();
  });

  it('shows green color for sustainable status', () => {
    const { container } = render(<KPICard value={0.65} status="sustainable" />);
    expect(container.firstChild).toHaveClass('status-green');
  });
});

describe('ExecutiveDashboard', () => {
  it('fetches and displays KPIs', async () => {
    // Mock API
    jest.spyOn(api, 'getExecutiveKPIs').mockResolvedValue(mockKPIs);
    
    render(<ExecutiveDashboard />);
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('9.72%')).toBeInTheDocument();
    });
  });
});
```

**End-to-End Tests (Playwright/Cypress):**
- Test complete user workflows
- Test authentication flow
- Test dashboard navigation
- Test data filtering and export

**Example E2E Test:**
```typescript
test('user can login and view executive dashboard', async ({ page }) => {
  // Navigate to login
  await page.goto('/login');
  
  // Fill credentials
  await page.fill('[name="username"]', 'testuser');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  
  // Verify redirect to dashboard
  await expect(page).toHaveURL('/dashboard/executive');
  
  // Verify KPIs are displayed
  await expect(page.locator('.kpi-card')).toHaveCount(4);
});
```

### Property-Based Testing

**Framework:** Hypothesis (Python backend)

**Property Tests:**

1. **Property 1 Test**: Generate random user credentials, verify token contains correct user ID
   - **Feature: interactive-dashboard-system, Property 1: Authentication token validity**

2. **Property 2 Test**: Generate random user roles and endpoints, verify access control rules
   - **Feature: interactive-dashboard-system, Property 2: Role-based access control**

3. **Property 3 Test**: Generate random trigger events, verify sum equals total count
   - **Feature: interactive-dashboard-system, Property 3: Dashboard data consistency**

4. **Property 4 Test**: Generate random payouts and premiums, verify loss ratio calculation
   - **Feature: interactive-dashboard-system, Property 4: Loss ratio calculation accuracy**

5. **Property 5 Test**: Generate random model metrics, verify ranking consistency
   - **Feature: interactive-dashboard-system, Property 5: Model comparison consistency**

6. **Property 6 Test**: Generate random forecasts, verify temporal ordering
   - **Feature: interactive-dashboard-system, Property 6: Trigger forecast temporal ordering**

7. **Property 7 Test**: Generate random valid requests, verify JSON response format
   - **Feature: interactive-dashboard-system, Property 7: API response format consistency**

8. **Property 8 Test**: Generate random invalid requests, verify error response structure
   - **Feature: interactive-dashboard-system, Property 8: Error response structure**

9. **Property 9 Test**: Generate random filters, verify export completeness
   - **Feature: interactive-dashboard-system, Property 9: Data export completeness**

10. **Property 10 Test**: Generate random pagination parameters, verify page size and offset
    - **Feature: interactive-dashboard-system, Property 10: Pagination correctness**

## Implementation Notes

### Security Considerations

**Authentication:**
- Use bcrypt with salt rounds = 12 for password hashing
- JWT tokens expire after 24 hours
- Implement refresh token mechanism for long sessions
- Store tokens in httpOnly cookies (not localStorage)

**Authorization:**
- Implement role-based access control (RBAC)
- Roles: admin (full access), analyst (read/write), viewer (read-only)
- Check permissions on every API request

**Input Validation:**
- Validate all user inputs using Pydantic
- Sanitize inputs to prevent SQL injection
- Use parameterized queries with SQLAlchemy ORM
- Implement rate limiting (100 requests/minute per user)

**HTTPS:**
- Enforce HTTPS in production
- Use Let's Encrypt for SSL certificates
- Redirect HTTP to HTTPS

**CORS:**
- Configure CORS to allow only frontend domain
- Don't use wildcard (*) in production

### Performance Optimization

**Backend:**
- Use database connection pooling (pool size = 20)
- Implement caching for frequently accessed data (Redis optional)
- Use database indexes on frequently queried columns
- Paginate large result sets (default page size = 50)
- Use async endpoints for I/O-bound operations

**Frontend:**
- Code splitting by route
- Lazy load dashboard components
- Memoize expensive computations
- Debounce user inputs (300ms)
- Use virtual scrolling for large lists
- Optimize chart rendering (max 1000 points per series)

**Database:**
- Create indexes on foreign keys
- Use EXPLAIN ANALYZE to optimize slow queries
- Implement data archiving for old records (>2 years)
- Regular VACUUM and ANALYZE operations

### Deployment Strategy

**Development Environment:**
```yaml
# docker-compose.dev.yml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/climate_dev
      - JWT_SECRET=dev_secret
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --reload --host 0.0.0.0
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
    command: npm run dev
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=climate_dev
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

**Production Environment:**
```yaml
# docker-compose.prod.yml
services:
  backend:
    image: climate-backend:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET=${JWT_SECRET}
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
  
  frontend:
    image: climate-frontend:latest
    depends_on:
      - backend
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
```

### Configuration Management

**Backend Configuration** (`.env`):
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/climate_db

# Authentication
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# File Paths
OUTPUTS_DIR=../outputs
MODELS_DIR=../outputs/models

# Logging
LOG_LEVEL=INFO
```

**Frontend Configuration** (`.env`):
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_TITLE=Tanzania Climate Prediction
```

### Migration Strategy

**Database Migrations (Alembic):**
```bash
# Create migration
alembic revision --autogenerate -m "create users table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

**Data Migration:**
- Load existing CSV data into PostgreSQL
- Create ETL script to populate database from outputs/
- Schedule periodic sync (daily) to keep database updated
