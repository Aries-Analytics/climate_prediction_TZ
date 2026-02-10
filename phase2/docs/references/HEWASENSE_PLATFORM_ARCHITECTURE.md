# HewaSense Platform Architecture - Summary

**Full Name**: HewaSense™ Climate Intelligence Platform  
**Tagline**: "Climate Intelligence Platform | Solution Workflow"

---

## System Components

### 1. HS-Core: Data Processing Pipeline
- Satellite data ingestion
- Data cleaning & feature engineering
- Risk indexing
- Outputs: Structured Features & Indices

### 2. HS-Models: Risk Modeling & Prediction  
- ML Algorithms (LSTM, RF)
- Ensemble modeling
- Uncertainty quantification
- Outputs: Climate Risk Signals & Probabilities

**Production Model**: Phase-based coverage (4 rice growth phases)
- Germination (21 days, 20% weight)
- Vegetative (29 days, 30% weight)
- Flowering (40 days, **35% weight** - most critical)
- Ripening (55 days, 15% weight)

### 3. HS-API & HS-Viz: Insight Delivery & Action
- **HS-API**: Secure endpoints & query service
- **HS-Viz**: Interactive dashboards, alerts & reports
- User decision support & action

---

## Dashboard Display Strategy

### Early Warning System (EWS) Dashboard
**What to show**:
- Seasonal forecast: Mar-Jun 2026
- Predicted rainfall: 385mm
- Drought probability: 35%
- Expected payout: $24.50/farmer
- **Phase breakdown** (4 phases with status)
  - ✅ Germination: Normal
  - ✅ Vegetative: Normal
  - ⚠️ Flowering: Drought risk ($28 payout)
  - ✅ Ripening: Normal
- Portfolio risk level: MEDIUM

### Trigger Events Dashboard
**What to show**:
- Historical trigger events (existing)
- Payout history by location (existing)
- Model validation metrics (after season)

---

## Key Clarifications

1. **HewaSense** = Entire platform name (not just the phase-based model)

2. **Phase-based coverage** = THE production model (not "alternative")
   - Simple 400mm threshold kept only in docs for validation

3. **Model comparison** = Development/validation tool only
   - Not displayed in production dashboards
   - Used in documentation to show improvement

4. **Branding**:
   - Platform: "HewaSense Climate Intelligence Platform"
   - Components: HS-Core, HS-Models, HS-API, HS-Viz
   - Don't say "HewaSense model" - say "phase-based coverage model"

---

**Document**: HewaSense Platform Architecture  
**Date**: January 23, 2026  
**Purpose**: Clarify system naming and structure
