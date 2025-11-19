# Tanzania Climate Prediction API Reference

## Base URL
- Development: `http://localhost:8000`
- Production: `https://your-domain.com`

## Authentication

All endpoints (except `/` and `/health`) require JWT authentication.

### Get Token
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Use Token
Include the token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## API Endpoints

### Authentication

#### Register User
```
POST /api/auth/register
```
**Body:**
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string",
  "role": "admin|analyst|viewer"
}
```

#### Login
```
POST /api/auth/login
```
**Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

#### Get Current User
```
GET /api/auth/me
```

---

### Dashboard

#### Executive KPIs
```
GET /api/dashboard/executive
```
**Response:**
```json
{
  "flood_trigger_rate": {
    "trigger_type": "flood",
    "rate": 0.12,
    "count": 45,
    "target_min": 0.05,
    "target_max": 0.15,
    "status": "within_target"
  },
  "drought_trigger_rate": {...},
  "crop_failure_trigger_rate": {...},
  "combined_trigger_rate": 0.28,
  "loss_ratio": 0.65,
  "sustainability_status": "sustainable",
  "total_triggers_ytd": 135,
  "estimated_payouts_ytd": 650000.0
}
```

#### Loss Ratio Trend
```
GET /api/dashboard/triggers/trend?months=12
```

#### Sustainability Status
```
GET /api/dashboard/sustainability
```

---

### Models

#### List All Models
```
GET /api/models
```

#### Get Model Metrics
```
GET /api/models/{model_name}/metrics
```
**Response:**
```json
{
  "model_name": "random_forest",
  "r2_score": 0.85,
  "rmse": 12.5,
  "mae": 8.3,
  "mape": 15.2,
  "training_date": "2024-01-15T10:30:00Z",
  "experiment_id": "exp_123"
}
```

#### Get Feature Importance
```
GET /api/models/{model_name}/importance
```

#### Check Model Drift
```
GET /api/models/{model_name}/drift?threshold=0.1
```

#### Get Prediction History
```
GET /api/models/{model_name}/predictions?limit=100
```

#### Compare Models
```
GET /api/models/compare?model_names=rf&model_names=xgb&metric=r2_score
```

---

### Triggers

#### List Trigger Events
```
GET /api/triggers?start_date=2024-01-01&end_date=2024-12-31&event_type=drought&skip=0&limit=100
```
**Query Parameters:**
- `start_date` (optional): Filter by start date
- `end_date` (optional): Filter by end date
- `event_type` (optional): Filter by type (drought, flood, crop_failure)
- `skip` (optional): Pagination offset (default: 0)
- `limit` (optional): Page size (default: 100, max: 1000)

#### Count Trigger Events
```
GET /api/triggers/count?start_date=2024-01-01&end_date=2024-12-31
```

#### Get Timeline
```
GET /api/triggers/timeline?start_date=2024-01-01&end_date=2024-12-31
```

#### Get Forecasts
```
GET /api/triggers/forecast?months_ahead=3
```
**Response:**
```json
[
  {
    "target_date": "2024-06-15",
    "trigger_type": "drought",
    "probability": 0.75,
    "confidence_lower": 0.65,
    "confidence_upper": 0.85
  }
]
```

#### Get Early Warnings
```
GET /api/triggers/warnings?threshold=0.7
```

#### Export to CSV
```
GET /api/triggers/export?start_date=2024-01-01&end_date=2024-12-31
```

---

### Climate

#### Get Time Series
```
GET /api/climate/timeseries?variable=rainfall&start_date=2024-01-01&end_date=2024-12-31
```
**Variables:** `temperature`, `rainfall`, `ndvi`, `enso`, `iod`

#### Get Anomalies
```
GET /api/climate/anomalies?variable=temperature&threshold=2.0
```

#### Get Correlations
```
GET /api/climate/correlations?variables=rainfall&variables=ndvi&variables=temperature
```
**Response:**
```json
{
  "variables": ["rainfall", "ndvi", "temperature"],
  "matrix": [
    [1.0, 0.65, -0.32],
    [0.65, 1.0, -0.28],
    [-0.32, -0.28, 1.0]
  ]
}
```

#### Get Seasonal Patterns
```
GET /api/climate/seasonal?variable=rainfall
```

---

### Risk

#### Get Portfolio Metrics
```
GET /api/risk/portfolio
```
**Response:**
```json
{
  "total_premium_income": 1000000.0,
  "expected_payouts": 650000.0,
  "loss_ratio": 0.65,
  "total_policies": 1000,
  "active_policies": 950,
  "trigger_distribution": {
    "drought": 45,
    "flood": 30,
    "crop_failure": 25
  },
  "geographic_distribution": {
    "Northern": 250,
    "Central": 300,
    "Southern": 200,
    "Coastal": 200
  },
  "risk_score": 65.0
}
```

#### Run Scenario Analysis
```
POST /api/risk/scenario
```
**Body:**
```json
{
  "scenario_name": "Severe Drought",
  "rainfall_change_pct": -30.0,
  "temperature_change_celsius": 2.0,
  "duration_months": 6
}
```
**Response:**
```json
{
  "scenario_name": "Severe Drought",
  "parameters": {...},
  "estimated_triggers": 120,
  "estimated_payouts": 1200000.0,
  "projected_loss_ratio": 1.2,
  "risk_level": "high",
  "impact_summary": "Severe drought conditions would increase triggers by 150%..."
}
```

#### Get Recommendations
```
GET /api/risk/recommendations
```
**Response:**
```json
[
  {
    "priority": "high",
    "category": "risk_mitigation",
    "title": "Loss Ratio Exceeds Threshold",
    "description": "Current loss ratio (0.75) exceeds the sustainable threshold (0.70).",
    "action_items": [
      "Review and adjust premium rates",
      "Implement stricter underwriting criteria",
      "Consider reinsurance options"
    ]
  }
]
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE"
}
```

### Error Codes

| Code | Status | Description |
|------|--------|-------------|
| AUTH_001 | 401 | Authentication failed |
| AUTH_002 | 403 | Insufficient permissions |
| RES_001 | 404 | Resource not found |
| VAL_001 | 422 | Validation error |
| DB_001 | 503 | Database error |
| SRV_001 | 500 | Internal server error |

### Example Error Response

```json
{
  "detail": "Could not validate credentials",
  "error_code": "AUTH_001"
}
```

---

## Rate Limiting

- 100 requests per minute per user
- Exceeding the limit returns 429 Too Many Requests

---

## Pagination

Endpoints that return lists support pagination:

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Number of records to return (default: 100, max: 1000)

**Example:**
```
GET /api/triggers?skip=100&limit=50
```

---

## Data Formats

### Dates
ISO 8601 format: `YYYY-MM-DD`

Example: `2024-01-15`

### Timestamps
ISO 8601 format with timezone: `YYYY-MM-DDTHH:MM:SSZ`

Example: `2024-01-15T10:30:00Z`

### Decimals
Floating point numbers with up to 4 decimal places

Example: `0.8523`

---

## CORS

The API supports CORS for the following origins:
- `http://localhost:3000` (development)
- Your production domain (configured via environment variables)

---

## Health Check

```
GET /health
```
**Response:**
```json
{
  "status": "healthy"
}
```

Use this endpoint for monitoring and load balancer health checks.
