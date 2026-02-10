# Phase-Based Coverage Dashboard Update

**Date**: January 23, 2026  
**Purpose**: Display simple vs phase-based model comparison in risk management dashboard

---

## Dashboard Enhancement: Model Comparison Section

### New Section: "Insurance Model Comparison"

Add to risk management dashboard between "Risk Portfolio" and "Historical Triggers"

###Data Source

- **Endpoint**: `/api/v1/seasonal/forecast/{location}`
- **Service**: `seasonal_forecast_integration.py` → `generate_seasonal_forecast_from_pipeline()`

### Display Components

#### 1. Model Comparison Table

| Model | Method | Predicted Payout | Phases Triggered | Status |
|-------|--------|------------------|------------------|--------|
| Simple (Current) | 400mm threshold | $60 | N/A | ✓ Baseline |
| **Phase-Based (HewaSense)** | 4-phase weighted | **$75** | 2/4 | ⭐ **Recommended** |

#### 2. Phase Breakdown (Expandable Detail)

**Flowering Phase** (Most Critical - 35% weight):
- Rainfall: 75mm (Trigger: <80mm)
- Status: ⚠️ Drought risk detected
- Payout: $26.25

**Vegetative Phase** (30% weight):
- Rainfall: 95mm (Trigger: <70mm)
- Status: ✅ Normal
- Payout: $0

[...other phases...]

#### 3. Risk Comparison Chart

```
Drought Probability:
Simple:    ███████░░░ 32%
Phase-Based: ████████░░ 38%  ← More sensitive (better basis risk)
```

#### 4. Portfolio Impact Summary

**Based on Phase-Based Model**:
- Affected Farmers: 380/1,000 (38%)
- Expected  Payout: $28,500
- Reserve Requirement: $85,500
- Status: ✅ Within sustainable range

---

## Implementation Code

### Backend API Enhancement

**File**: `backend/app/api/v1/forecasts.py`

```python
from app.services.seasonal_forecast_integration import generate_seasonal_forecast_from_pipeline

@router.get("/seasonal/forecast/{location}")
def get_seasonal_forecast(
    location: str,
    db: Session = Depends(get_db)
):
    """Get seasonal forecast with phase-based model comparison"""
    
    # Get latest monthly forecasts
    monthly_forecasts = get_latest_monthly_forecasts(db, location)
    
    # Generate seasonal forecast Integration
    result = generate_seasonal_forecast_from_pipeline(
        db,
        location_id=get_location_id(location),
        year=2026,
        monthly_forecast_ids=[f.id for f in monthly_forecasts]
    )
    
    return result['dashboard_summary']
```

### Frontend Component (Conceptual)

**File**: `frontend/src/components/PhaseBasedModelComparison.jsx`

```javascript
// Fetch seasonal forecast
const { data } = useFetch('/api/v1/seasonal/forecast/Morogoro');

// Display comparison
<Card title="Insurance Model Comparison">
  <Table data={data.model_comparison} />
  
  <Expandable title="Phase Breakdown">
    {data.phase_breakdown.map(phase => (
      <PhaseCard
        name={phase.name}
        rainfall={phase.rainfall_mm}
        payout={phase.payout}
        status={phase.status}
      />
    ))}
  </Expandable>
  
  <RiskChart 
    drought_prob={data.trigger_probabilities.drought}
    model="phase_based"
  />
</Card>
```

---

## Sample Dashboard Data Response

```json
{
  "location": "Morogoro",
  "season": "Mar-Jun 2026",
  "predicted_rainfall": 380,
  
  "model_comparison": [
    {
      "model": "Simple (Current)",
      "method": "400mm threshold",
      "payout": 60,
      "triggered": true
    },
    {
      "model": "Phase-Based (HewaSense)",
      "method": "4-phase weighted",
      "payout": 75,
      "phases_triggered": 2,
      "recommended": true
    }
  ],
  
  "drought_risk": "38%",
  "flood_risk": "5%",
  "risk_level": "MEDIUM",
  "expected_payout_per_farmer": 28.50,
  
  "phase_breakdown": {
    "germination": {
      "rainfall_mm": 55,
      "drought_trigger": 40,
      "payout": 0,
      "status": "normal"
    },
    "vegetative": {
      "rainfall_mm": 95,
      "drought_trigger": 70,
      "payout": 0,
      "status": "normal"
    },
    "flowering": {
      "rainfall_mm": 75,
      "drought_trigger": 80,
      "payout": 26.25,
      "status": "drought_risk"
    },
    "ripening": {
      "rainfall_mm": 85,
      "drought_trigger": 60,
      "payout": 0,
      "status": "normal"
    }
  }
}
```

---

## Dashboard Location

**Current Dashboard**: Risk Management Dashboard  
**New Section**: Add after "risk_portfolio" and before "historical_triggers"

**Visual Priority**:
1. Model comparison table (prominent)
2. Risk level indicator
3. Expected payout (portfolio total)
4. Phase breakdown (expandable/collapsible)

---

## User Benefits

**For Farm Managers**:
- See which growth phase is at risk
- Understand why payout differs from simple model
- Better planning for critical periods

**For Insurers**:
- Compare model accuracy
- Validate basis risk reduction
- Transparent trigger methodology

**For Regulators**:
- Industry-standard methodology
- Phase-based = industry standard
- Clear justification for payouts

---

**Document**: Dashboard Integration Guide  
**Status**: Ready for frontend implementation  
**Backend**: Complete (seasonal_forecast_integration.py)
