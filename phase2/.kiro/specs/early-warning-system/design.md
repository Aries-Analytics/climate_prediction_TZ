# Early Warning System Design Document

## Overview

The Early Warning System (EWS) leverages trained ML models to forecast climate-related insurance triggers 3-6 months in advance. It provides probabilistic predictions with confidence intervals, actionable recommendations, and automated forecast generation to enable proactive risk management.

## Architecture

### System Components

1. **Forecast Generator Service**: Core prediction engine using trained ensemble models
2. **Forecast API**: REST endpoints for retrieving and managing forecasts
3. **Forecast Scheduler**: Automated job for regular forecast updates
4. **Validation Service**: Compares forecasts against actual outcomes
5. **Recommendation Engine**: Generates actionable advice based on predictions
6. **Forecast Dashboard**: UI for visualizing predictions and trends

### Data Flow

```
Climate Data → Feature Engineering → Ensemble Model → Forecast Generation → Database Storage → API/Dashboard
                                                    ↓
                                            Recommendation Engine
                                                    ↓
                                            Validation Service (post-event)
```

## Components and Interfaces

### 1. Forecast Generator Service

**Purpose**: Generate probabilistic forecasts using trained ML models

**Key Functions**:
- `generate_forecasts(start_date, horizons=[3,4,5,6])`: Create predictions for multiple time horizons
- `calculate_confidence_intervals(predictions, model_uncertainty)`: Compute upper/lower bounds
- `ensemble_predict(features)`: Combine predictions from multiple models

**Inputs**:
- Latest climate data (temperature, rainfall, NDVI, ENSO, IOD)
- Trained model artifacts from MLflow
- Forecast horizons (months ahead)

**Outputs**:
- Trigger probabilities (0-1) for each type and horizon
- Confidence intervals (lower, upper bounds)
- Model uncertainty metrics

### 2. Forecast API Endpoints

```
GET /api/forecasts
  Query params: trigger_type, min_probability, horizon_months, start_date, end_date
  Response: List of forecast objects with probabilities and confidence intervals

GET /api/forecasts/latest
  Response: Most recent forecasts for all trigger types and horizons

GET /api/forecasts/recommendations
  Query params: min_probability
  Response: Actionable recommendations for high-risk forecasts

GET /api/forecasts/validation
  Query params: start_date, end_date
  Response: Forecast accuracy metrics and validation results

POST /api/forecasts/generate
  Body: { start_date, horizons }
  Response: Newly generated forecasts
```

### 3. Database Schema

**Table: forecasts**
```sql
CREATE TABLE forecasts (
    id SERIAL PRIMARY KEY,
    forecast_date DATE NOT NULL,
    target_date DATE NOT NULL,
    horizon_months INTEGER NOT NULL,
    trigger_type VARCHAR(50) NOT NULL,
    probability DECIMAL(5,4) NOT NULL,
    confidence_lower DECIMAL(5,4) NOT NULL,
    confidence_upper DECIMAL(5,4) NOT NULL,
    model_version VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(forecast_date, target_date, trigger_type)
);

CREATE INDEX idx_forecasts_target ON forecasts(target_date, trigger_type);
CREATE INDEX idx_forecasts_created ON forecasts(created_at);
```

**Table: forecast_recommendations**
```sql
CREATE TABLE forecast_recommendations (
    id SERIAL PRIMARY KEY,
    forecast_id INTEGER REFERENCES forecasts(id),
    recommendation_text TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL,
    action_timeline VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Table: forecast_validation**
```sql
CREATE TABLE forecast_validation (
    id SERIAL PRIMARY KEY,
    forecast_id INTEGER REFERENCES forecasts(id),
    actual_trigger_id INTEGER REFERENCES trigger_events(id),
    was_correct BOOLEAN NOT NULL,
    probability_error DECIMAL(5,4),
    brier_score DECIMAL(5,4),
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Data Models

### Forecast Model
```python
class Forecast:
    id: int
    forecast_date: date  # When forecast was made
    target_date: date    # Date being predicted
    horizon_months: int  # 3, 4, 5, or 6
    trigger_type: str    # drought, flood, crop_failure
    probability: float   # 0.0 to 1.0
    confidence_lower: float
    confidence_upper: float
    model_version: str
    created_at: datetime
```

### Recommendation Model
```python
class Recommendation:
    id: int
    forecast_id: int
    recommendation_text: str
    priority: str  # high, medium, low
    action_timeline: str
    created_at: datetime
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Forecast probability bounds
*For any* generated forecast, the probability value must be between 0 and 1 inclusive, and confidence_lower ≤ probability ≤ confidence_upper
**Validates: Requirements 1.3**

### Property 2: Forecast horizon consistency
*For any* forecast with horizon_months = N, the target_date must equal forecast_date plus N months
**Validates: Requirements 1.1**

### Property 3: Confidence interval validity
*For any* forecast, the confidence interval width (confidence_upper - confidence_lower) must be non-negative and less than 1.0
**Validates: Requirements 2.1, 2.3**

### Property 4: Recommendation threshold
*For any* forecast with probability > 0.3, the system must generate at least one recommendation
**Validates: Requirements 3.1, 3.2, 3.3**

### Property 5: Forecast freshness
*For any* API request for latest forecasts, all returned forecasts must have created_at within the last 7 days
**Validates: Requirements 4.2**

### Property 6: Validation completeness
*For any* actual trigger event, if a forecast existed for that date and trigger type, a validation record must be created
**Validates: Requirements 6.1**

### Property 7: API response schema
*For any* successful API forecast request, the response must conform to the defined JSON schema with all required fields present
**Validates: Requirements 5.1**

## Error Handling

1. **Missing Climate Data**: If recent data is unavailable, use last known values with increased uncertainty
2. **Model Loading Failures**: Fall back to simpler baseline model (historical averages)
3. **Forecast Generation Timeout**: Cancel after 5 minutes, log error, alert admin
4. **Invalid Probability Values**: Clip to [0, 1] range and log warning
5. **Database Connection Errors**: Retry 3 times with exponential backoff, then fail gracefully

## Testing Strategy

### Unit Tests
- Test forecast probability calculations with known inputs
- Test confidence interval computation
- Test recommendation generation logic
- Test date arithmetic for horizon calculations
- Test API request/response serialization

### Property-Based Tests
- Use Hypothesis library for Python
- Generate random climate data and verify all forecasts have valid probabilities
- Generate random dates and verify horizon calculations are correct
- Generate random forecasts and verify confidence intervals are valid
- Test that high-probability forecasts always generate recommendations

### Integration Tests
- Test end-to-end forecast generation from climate data to database storage
- Test API endpoints with various query parameters
- Test forecast validation against actual trigger events
- Test automated scheduler triggers forecast regeneration
- Test recommendation engine with different probability thresholds

### Performance Tests
- Verify forecast generation completes within 5 minutes for all horizons
- Test API response times under load (100 concurrent requests)
- Verify database queries use indexes efficiently

## Implementation Notes

1. **Model Loading**: Load trained ensemble model from MLflow on service startup, cache in memory
2. **Feature Engineering**: Reuse existing preprocessing pipeline from training
3. **Uncertainty Quantification**: Use model ensemble variance + calibration curves
4. **Caching**: Cache latest forecasts for 1 hour to reduce database load
5. **Monitoring**: Track forecast generation time, API latency, validation accuracy
6. **Alerting**: Send notifications when forecast accuracy drops below 60% or generation fails
