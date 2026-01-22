# Future Enhancement: Dynamic Policy Configuration System

**Priority:** Medium  
**Effort:** 2-3 days  
**Impact:** High (Production Readiness)

---

## Current State

**Hardcoded Constants in `risk_service.py`:**
```python
PILOT_LOCATION_ID = 6
TOTAL_FARMERS = 1000
CURRENT_RESERVES = 150000
PAYOUT_RATES = {
    "drought": 60,
    "flood": 75,
    "crop_failure": 90
}
PREMIUM_PER_FARMER = 91  # Validated sustainable premium
HIGH_RISK_THRESHOLD = 0.75
```

**Problem:**
- Changing premiums requires code deployment
- No historical tracking of premium changes
- Can't A/B test different pricing strategies
- No per-location or per-product customization

---

## Proposed Solution

### Database Schema

#### `policy_config` Table
```sql
CREATE TABLE policy_config (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    premium_per_farmer DECIMAL(10, 2) NOT NULL,
    effective_date DATE NOT NULL,
    expiry_date DATE,
    max_payout DECIMAL(10, 2),
    reserves_target DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(100)
);
```

#### `payout_rates` Table
```sql
CREATE TABLE payout_rates (
    id SERIAL PRIMARY KEY,
    trigger_type VARCHAR(50) NOT NULL,
    payout_amount DECIMAL(10, 2) NOT NULL,
    effective_date DATE NOT NULL,
    expiry_date DATE,
    location_id INTEGER REFERENCES locations(id)
);
```

### API Endpoints

**Admin Configuration:**
```
POST   /api/admin/policy-config          # Create new policy config
PUT    /api/admin/policy-config/{id}     # Update existing config
GET    /api/admin/policy-config/history  # View historical configs
```

**Runtime Retrieval:**
```python
def get_active_config(db: Session, location_id: int) -> PolicyConfig:
    """Get active policy configuration for a location"""
    today = date.today()
    return db.query(PolicyConfig).filter(
        PolicyConfig.location_id == location_id,
        PolicyConfig.effective_date <= today,
        (PolicyConfig.expiry_date.is_(None) | (PolicyConfig.expiry_date >= today))
    ).order_by(PolicyConfig.effective_date.desc()).first()
```

### Migration Path

1. **Phase 1 (Backward Compatible):**
   - Create tables
   - Seed with current constants ($91 premium, existing payout rates)
   - Update `risk_service.py` to **try database first, fallback to constants**
   
2. **Phase 2 (Admin UI):**
   - Build admin panel for configuration management
   - Add audit logging for config changes
   
3. **Phase 3 (Remove Constants):**
   - Delete hardcoded constants
   - Make database the single source of truth

---

## Benefits

✅ **Flexibility:** Change premiums without redeployment  
✅ **Auditability:** Track who changed what and when  
✅ **Multi-Tenant:** Support different rates per location/product  
✅ **Testing:** Easy A/B testing of pricing strategies  
✅ **Compliance:** Historical record of all pricing decisions

---

## Implementation Checklist

- [ ] Create database models (`PolicyConfig`, `PayoutRate`)
- [ ] Write Alembic migration
- [ ] Seed initial data from current constants
- [ ] Update `risk_service.py` to query database
- [ ] Add admin API endpoints
- [ ] Build admin UI panel
- [ ] Write integration tests
- [ ] Document API in OpenAPI spec
- [ ] Remove hardcoded constants

---

## Related Files

- `backend/app/services/risk_service.py` (current constants)
- `backend/app/models/` (new models needed)
- `backend/alembic/versions/` (migration needed)
- `docs/references/PREMIUM_SUSTAINABILITY_ANALYSIS.md` (premium validation)

---

**Created:** 2026-01-22  
**Status:** Proposed  
**Acceptance Criteria:** Premium can be changed via admin UI without code deployment
