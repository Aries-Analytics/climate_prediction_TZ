# Tanzania Climate Prediction API Documentation

## Overview

The Tanzania Climate Prediction API provides endpoints for climate insights, ML model monitoring, insurance trigger management, and risk analysis. The API is built with FastAPI and follows RESTful principles.

**Base URL**: `http://localhost:8000/api`

**API Version**: 1.0.0

## Authentication

All endpoints (except `/auth/login` and `/auth/register`) require JWT authentication.

### Obtaining a Token

**POST** `/auth/login`

```json
{
  "username": "user@example.com",
  "password": "your_password"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "user@example.com",
    "email": "user@example.com",
    "role": "analyst"
  }
}
```

### Using the Token

Include the token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## API Endpoints

### Authentication

#### Register New User

**POST** `/auth/register`

Creates a new user account.

**Request Body**:
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "SecurePassword123!",
  "role": "analyst"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "username": "newuser",
  "email": "newuser@example.com",
  "role": "analyst",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Login

**POST** `/auth/login`

Authenticates user and returns JWT token.

**Request Body**:
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "user@example.com",
    "email": "user@example.com",
    "role": "analyst"
  }
}
```

#### Get Current User

**GET** `/auth/me`

Returns information about the currently authenticated user.

**Response** (200 OK):
```json
{
  "id": 1,
  "username": "user@example.com",
  "email": "user@example.com",
  "role": "analyst",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### Dashboard

#### Get Executive KPIs

**GET** `/dashboard/executive`

Returns key performance indicators for executive dashboard.

**Response** (200 OK):
```json
{
  "total_triggers": 45,
  "trigger_rate": 0.15,
  "loss_ratio": 0.82,
  "sustainability_status": "sustainable",
  "total_payouts": 125000.50,
  "avg_payout": 2777.79,
  "period": "last_12_months"
}
```

**Caching**: Results are cached for 5 minutes.

#### Get Loss Ratio Trend

**GET** `/dashboard/triggers/trend?months=12`

Returns loss ratio trend over time.

**Query Parameters**:
- `months` (integer, default: 12): Number of months to include

**Response** (200 OK):
```json
{
  "months": ["2023-01", "2023-02", "2023-03", ...],
  "loss_ratios": [0.75, 0.82, 0.68, ...],
  "trigger_counts": [3, 5, 2, ...],
  "payout_amounts": [8500.00, 12000.00, 5500.00, ...]
}
```

#### Get Sustainability Status

**GET** `/dashboard/sustainability`

Returns sustainability assessment of the insurance program.

**Response** (200 OK):
```json
{
  "status": "sustainable",
  "loss_ratio": 0.82,
  "threshold": 0.85,
  "recommendation": "Program is sustainable. Continue monitoring.",
  "risk_level": "low"
}
```

---

### Models

#### List All Models

**GET** `/models`

Returns list of all ML models with their metrics.

**Response** (200 OK):
```json
{
  "models": [
    {
      "name": "random_forest_v1",
      "type": "classification",
      "accuracy": 0.87,
      "precision": 0.85,
      "recall": 0.89,
      "f1_score": 0.87,
      "created_at": "2024-01-10T08:00:00Z",
      "status": "active"
    },
    ...
  ]
}
```

#### Get Model Metrics

**GET** `/models/{model_name}/metrics`

Returns detailed metrics for a specific model.

**Path Parameters**:
- `model_name` (string): Name of the model

**Response** (200 OK):
```json
{
  "model_name": "random_forest_v1",
  "metrics": {
    "accuracy": 0.87,
    "precision": 0.85,
    "recall": 0.89,
    "f1_score": 0.87,
    "auc_roc": 0.92
  },
  "confusion_matrix": [[45, 5], [3, 47]],
  "training_date": "2024-01-10T08:00:00Z",
  "data_version": "v2.1"
}
```

#### Get Feature Importance

**GET** `/models/{model_name}/importance`

Returns feature importance scores for a model.

**Response** (200 OK):
```json
{
  "model_name": "random_forest_v1",
  "features": [
    {"name": "rainfall_mm", "importance": 0.35},
    {"name": "temperature_avg", "importance": 0.28},
    {"name": "ndvi", "importance": 0.22},
    {"name": "enso_index", "importance": 0.15}
  ]
}
```

#### Compare Models

**POST** `/models/compare`

Compares multiple models side-by-side.

**Request Body**:
```json
{
  "model_names": ["random_forest_v1", "xgboost_v1", "logistic_regression_v1"],
  "metrics": ["accuracy", "precision", "recall", "f1_score"]
}
```

**Response** (200 OK):
```json
{
  "comparison": [
    {
      "model_name": "random_forest_v1",
      "accuracy": 0.87,
      "precision": 0.85,
      "recall": 0.89,
      "f1_score": 0.87
    },
    ...
  ],
  "best_model": "random_forest_v1",
  "best_metric": "f1_score"
}
```

---

### Triggers

#### List Trigger Events

**GET** `/triggers?start_date=2024-01-01&end_date=2024-12-31&trigger_type=drought&page=1&page_size=50`

Returns paginated list of trigger events with filters.

**Query Parameters**:
- `start_date` (date, optional): Filter by start date
- `end_date` (date, optional): Filter by end date
- `trigger_type` (string, optional): Filter by type (drought, flood, crop_failure)
- `page` (integer, default: 1): Page number
- `page_size` (integer, default: 50): Items per page

**Response** (200 OK):
```json
{
  "triggers": [
    {
      "id": 1,
      "date": "2024-03-15",
      "trigger_type": "drought",
      "confidence": 0.92,
      "severity": 0.85,
      "payout_amount": 5000.00,
      "location_lat": -6.3690,
      "location_lon": 34.8888,
      "created_at": "2024-03-15T12:00:00Z"
    },
    ...
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_items": 145,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  }
}
```

#### Get Trigger Timeline

**GET** `/triggers/timeline?start_date=2024-01-01&end_date=2024-12-31`

Returns timeline view of trigger events.

**Response** (200 OK):
```json
{
  "timeline": [
    {
      "date": "2024-03-15",
      "events": [
        {
          "id": 1,
          "trigger_type": "drought",
          "severity": 0.85,
          "payout_amount": 5000.00
        }
      ]
    },
    ...
  ]
}
```

#### Get Trigger Forecast

**GET** `/triggers/forecast?days=30`

Returns forecasted trigger probabilities.

**Query Parameters**:
- `days` (integer, default: 30): Number of days to forecast

**Response** (200 OK):
```json
{
  "forecast": [
    {
      "date": "2024-04-01",
      "drought_probability": 0.15,
      "flood_probability": 0.05,
      "crop_failure_probability": 0.08,
      "confidence_interval": [0.10, 0.20]
    },
    ...
  ],
  "model_used": "random_forest_v1",
  "generated_at": "2024-03-15T10:00:00Z"
}
```

#### Export Triggers

**GET** `/triggers/export?format=csv&start_date=2024-01-01&end_date=2024-12-31`

Exports trigger events in specified format.

**Query Parameters**:
- `format` (string): Export format (csv, json, excel)
- `start_date` (date, optional): Filter by start date
- `end_date` (date, optional): Filter by end date
- `trigger_type` (string, optional): Filter by type

**Response**: File download

---

### Climate

#### Get Time Series Data

**GET** `/climate/timeseries?variable=temperature_avg&start_date=2024-01-01&end_date=2024-12-31&max_points=1000`

Returns time series data for a climate variable (optimized for chart rendering).

**Query Parameters**:
- `variable` (string, required): Climate variable (temperature_avg, rainfall_mm, ndvi, enso_index, iod_index)
- `start_date` (date, optional): Start date
- `end_date` (date, optional): End date
- `max_points` (integer, default: 1000): Maximum data points for optimization

**Response** (200 OK):
```json
{
  "variable": "temperature_avg",
  "data": [
    {"date": "2024-01-01", "value": 28.5},
    {"date": "2024-01-02", "value": 29.1},
    ...
  ],
  "statistics": {
    "mean": 28.7,
    "median": 28.5,
    "std": 2.3,
    "min": 24.1,
    "max": 33.2
  },
  "optimized": true,
  "original_count": 365
}
```

**Note**: Data is automatically downsampled if it exceeds `max_points` for optimal chart rendering.

#### Get Anomalies

**GET** `/climate/anomalies?variable=rainfall_mm&threshold=2.0`

Detects anomalies in climate data.

**Query Parameters**:
- `variable` (string, required): Climate variable
- `threshold` (float, default: 2.0): Standard deviation threshold

**Response** (200 OK):
```json
{
  "variable": "rainfall_mm",
  "anomalies": [
    {
      "date": "2024-03-15",
      "value": 150.5,
      "expected": 45.2,
      "deviation": 3.2,
      "type": "high"
    },
    ...
  ],
  "threshold": 2.0
}
```

#### Get Correlations

**GET** `/climate/correlations?variables=temperature_avg&variables=rainfall_mm&variables=ndvi`

Calculates correlation matrix for climate variables.

**Query Parameters**:
- `variables` (array of strings): Variables to correlate

**Response** (200 OK):
```json
{
  "correlation_matrix": {
    "temperature_avg": {
      "temperature_avg": 1.0,
      "rainfall_mm": -0.45,
      "ndvi": -0.62
    },
    "rainfall_mm": {
      "temperature_avg": -0.45,
      "rainfall_mm": 1.0,
      "ndvi": 0.78
    },
    "ndvi": {
      "temperature_avg": -0.62,
      "rainfall_mm": 0.78,
      "ndvi": 1.0
    }
  }
}
```

#### Get Seasonal Patterns

**GET** `/climate/seasonal?variable=rainfall_mm`

Returns seasonal patterns for a climate variable.

**Response** (200 OK):
```json
{
  "variable": "rainfall_mm",
  "seasonal_averages": {
    "January": 85.2,
    "February": 92.5,
    "March": 125.8,
    ...
  },
  "peak_month": "March",
  "low_month": "July"
}
```

---

### Risk Management

#### Get Portfolio Metrics

**GET** `/risk/portfolio`

Returns risk portfolio metrics.

**Response** (200 OK):
```json
{
  "total_exposure": 1500000.00,
  "expected_payouts": 123000.00,
  "risk_concentration": {
    "drought": 0.65,
    "flood": 0.25,
    "crop_failure": 0.10
  },
  "geographic_distribution": [
    {"region": "Dodoma", "exposure": 450000.00},
    {"region": "Arusha", "exposure": 350000.00},
    ...
  ]
}
```

#### Run Scenario Analysis

**POST** `/risk/scenario`

Runs scenario analysis for risk assessment.

**Request Body**:
```json
{
  "scenario_name": "severe_drought",
  "parameters": {
    "rainfall_reduction": 0.40,
    "temperature_increase": 2.5,
    "duration_months": 6
  }
}
```

**Response** (200 OK):
```json
{
  "scenario_name": "severe_drought",
  "estimated_triggers": 25,
  "estimated_payouts": 625000.00,
  "loss_ratio": 1.15,
  "sustainability_impact": "high_risk",
  "recommendations": [
    "Consider increasing premiums by 15%",
    "Implement additional risk mitigation measures",
    "Review coverage limits"
  ]
}
```

#### Get Risk Recommendations

**GET** `/risk/recommendations`

Returns risk management recommendations.

**Response** (200 OK):
```json
{
  "recommendations": [
    {
      "priority": "high",
      "category": "pricing",
      "recommendation": "Adjust premiums for drought-prone regions",
      "impact": "Reduce loss ratio by 0.10"
    },
    ...
  ],
  "generated_at": "2024-03-15T10:00:00Z"
}
```

---

### Admin

#### List Users

**GET** `/admin/users`

Returns list of all users (admin only).

**Response** (200 OK):
```json
{
  "users": [
    {
      "id": 1,
      "username": "user1",
      "email": "user1@example.com",
      "role": "analyst",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z"
    },
    ...
  ]
}
```

#### Create User

**POST** `/admin/users`

Creates a new user (admin only).

**Request Body**:
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "SecurePassword123!",
  "role": "analyst"
}
```

#### Update User

**PUT** `/admin/users/{user_id}`

Updates user information (admin only).

**Request Body**:
```json
{
  "role": "admin",
  "is_active": true
}
```

#### Delete User

**DELETE** `/admin/users/{user_id}`

Deletes a user (admin only).

**Response** (204 No Content)

#### Get Audit Logs

**GET** `/admin/audit-logs?user_id=1&action=login&start_date=2024-01-01&page=1&page_size=50`

Returns audit logs with filters (admin only).

**Query Parameters**:
- `user_id` (integer, optional): Filter by user
- `action` (string, optional): Filter by action type
- `start_date` (date, optional): Filter by start date
- `end_date` (date, optional): Filter by end date
- `page` (integer, default: 1): Page number
- `page_size` (integer, default: 50): Items per page

**Response** (200 OK):
```json
{
  "logs": [
    {
      "id": 1,
      "user_id": 1,
      "action": "login",
      "resource": "/api/auth/login",
      "details": {"ip_address": "192.168.1.1"},
      "timestamp": "2024-03-15T10:30:00Z"
    },
    ...
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_items": 1250,
    "total_pages": 25
  }
}
```

---

## Error Responses

All endpoints return consistent error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters",
  "error_code": "VALIDATION_ERROR"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated",
  "error_code": "AUTHENTICATION_ERROR"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions",
  "error_code": "AUTHORIZATION_ERROR"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found",
  "error_code": "NOT_FOUND"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "error_code": "INTERNAL_ERROR"
}
```

---

## Rate Limiting

API requests are rate-limited to 100 requests per minute per user. Exceeding this limit returns a 429 Too Many Requests response.

---

## Caching

Certain endpoints implement caching to improve performance:

- Dashboard endpoints: 5 minutes TTL
- Model metrics: 10 minutes TTL
- Climate data: 15 minutes TTL

Cached responses include a `X-Cache-Hit` header indicating cache status.

---

## Interactive API Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These interfaces allow you to explore and test API endpoints directly from your browser.

---

## Support

For API support or questions, contact: support@example.com
