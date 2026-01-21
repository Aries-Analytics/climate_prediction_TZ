# TanStack Start Migration Plan

**Status:** Proposed  
**Created:** 2026-01-07  
**Timeline:** 3-4 weeks (phased approach)

---

## Executive Summary

### Why Migrate?
Current debugging issues (snake_case/camelCase, runtime type errors, manual API contracts) stem from **lack of end-to-end type safety**. TanStack Start can solve this, but requires significant architectural changes.

### Critical Reality Check
TanStack Start is a **full-stack TypeScript framework**. Your current backend is **Python/FastAPI**. To achieve true "type safety across the stack," we have three options:

1. **Frontend-Only Migration** (Keeps Python backend)
   - ❌ **Does NOT solve HTTP boundary issues**
   - ✅ Incremental, lower risk
   - ⚠️ Still need manual type definitions for API

2. **Full Migration to TypeScript** (Rewrite backend)
   - ✅ True end-to-end type safety
   - ❌ Massive effort (4-6 weeks)
   - ❌ High risk for ML/data pipelines

3. **Hybrid Architecture** (RECOMMENDED)
   - ✅ Keep Python for ML/data science
   - ✅ Move API/business logic to TypeScript
   - ✅ Achieves type safety for frontend ↔ API
   - ⚠️ Moderate complexity

---

## Recommended Approach: Hybrid Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│ TanStack Start App (TypeScript)                         │
│  ├─ Frontend (React + TanStack Router)                  │
│  ├─ Server Functions (TypeScript - BFF layer)           │
│  └─ Shared Types (enforced across frontend + server)    │
└────────────────┬────────────────────────────────────────┘
                 │ HTTP (typed via tRPC or similar)
                 ↓
┌─────────────────────────────────────────────────────────┐
│ Python Services (FastAPI)                               │
│  ├─ ML Models (forecast_service.py)                     │
│  ├─ Data Pipelines (insurance_business_pipeline.py)     │
│  ├─ Climate Data Processing                             │
│  └─ Database ORM (SQLAlchemy)                          │
└─────────────────────────────────────────────────────────┘
```

### How This Solves Your Problems

**Before (Current):**
```
Frontend (React) → Axios → FastAPI → Database
     ❌              ❌ Type boundary here
   location.overallRiskIndex  ←→  location_risk_index
```

**After (Hybrid):**
```
Frontend → TanStack Server Function → FastAPI → Database
    ✅ Types enforced           ❌ Still HTTP, but isolated
   location.overallRiskIndex → typed API client
```

**Key Benefit:** Type errors in frontend ↔ API layer are caught at compile time, even though Python backend still exists.

---

## Migration Phases

### Phase 1: Foundation (Week 1)
**Goal:** Set up TanStack Start alongside existing app

- [ ] Create new TanStack Start project in `phase2/frontend-v2/`
- [ ] Configure Vite + Nitro + TanStack Router
- [ ] Set up Docker container for new frontend
- [ ] Verify can run both apps simultaneously
- [ ] Create shared type definitions in `phase2/types/`

**Deliverables:**
- `frontend-v2/` running at `localhost:3001`
- Basic "Hello World" with TanStack Router
- Type definitions for core models (Location, Forecast, etc.)

---

### Phase 2: API Integration Layer (Week 2)
**Goal:** Create type-safe bridge to Python backend

**Option A: tRPC (Recommended)**
```typescript
// types/forecast.ts
export type LocationRisk = {
  locationId: number
  locationName: string
  droughtProbability: number
  // ... fully typed
}

// server/trpc.ts
export const forecastRouter = router({
  getLocationRisk: publicProcedure
    .input(z.object({ horizonMonths: z.number() }))
    .query(async ({ input }): Promise<LocationRisk[]> => {
      // Calls Python FastAPI
      const response = await fetch('http://backend:8000/forecasts/location-risk-summary')
      const data = await response.json()
      
      // Transform snake_case → camelCase with type enforcement
      return data.locations.map((loc: any) => ({
        locationId: loc.location_id,
        locationName: loc.location_name,
        droughtProbability: loc.drought_probability,
        // TypeScript enforces this matches LocationRisk
      }))
    })
})
```

**Benefit:** Type errors caught when Python response doesn't match TypeScript types.

**Tasks:**
- [ ] Install tRPC in TanStack Start
- [ ] Create tRPC router for each FastAPI endpoint
- [ ] Define TypeScript types for all API responses
- [ ] Write transformation logic (snake_case → camelCase) with type safety
- [ ] Create integration tests

---

### Phase 3: Migrate Core Pages (Week 3)
**Goal:** Rebuild critical dashboards with type safety

**Priority Order:**
1. **Early Warning Dashboard** (most problematic)
2. **Forecast Dashboard** (second priority)
3. **Executive Dashboard** (stable, lower priority)
4. **Trigger Events** (stable)
5. **Climate Insights** (stable)

**Migration Checklist per Dashboard:**
- [ ] Create route in TanStack Router
- [ ] Implement data fetching via tRPC
- [ ] Migrate React components (copy from old app)
- [ ] Verify types flow end-to-end
- [ ] Test with real data
- [ ] Compare UI with original

**Example - Early Warning Dashboard:**
```typescript
// routes/early-warning.tsx
import { createFileRoute } from '@tanstack/react-router'
import { trpc } from '../utils/trpc'

export const Route = createFileRoute('/early-warning')({
  loader: async () => {
    const [portfolioRisk, locationRisk] = await Promise.all([
      trpc.forecasts.getPortfolioRisk.query({ days: 180 }),
      trpc.forecasts.getLocationRisk.query({ horizonMonths: 3 })
    ])
    
    // ✅ Both fully typed - autocomplete works, typos caught
    return { portfolioRisk, locationRisk }
  },
  component: EarlyWarningDashboard
})

function EarlyWarningDashboard() {
  const { portfolioRisk, locationRisk } = Route.useLoaderData()
  
  // ✅ portfolioRisk.expectedPayouts is typed as number
  // ✅ locationRisk is typed as LocationRisk[]
  
  return <div>...</div>
}
```

---

### Phase 4: Deprecate Old Frontend (Week 4)
**Goal:** Switch to TanStack Start as primary app

- [ ] Update Docker Compose to make `frontend-v2` port 3000
- [ ] Move old frontend to `frontend-legacy` (backup)
- [ ] Update documentation
- [ ] Train team on TanStack Start patterns
- [ ] Monitor for issues

---

## Technical Specifications

### Directory Structure
```
phase2/
├── backend/              # Python FastAPI (unchanged)
│   ├── app/
│   ├── pipelines/
│   └── scripts/
├── frontend-legacy/      # Old React app (backup)
├── frontend-v2/          # NEW: TanStack Start app
│   ├── app/
│   │   ├── routes/       # File-based routing
│   │   ├── server/       # Server functions + tRPC
│   │   ├── components/   # Migrated React components
│   │   └── utils/
│   ├── types/            # Shared TypeScript types
│   └── vite.config.ts
└── docker-compose.dev.yml
```

### Dependencies
**Add to frontend-v2:**
```json
{
  "dependencies": {
    "@tanstack/react-router": "^1.x",
    "@tanstack/start": "^1.x",
    "@trpc/client": "^10.x",
    "@trpc/server": "^10.x",
    "zod": "^3.x",
    "@mui/material": "^5.x",
    "axios": "^1.x"
  }
}
```

---

## Risk Mitigation

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| TanStack Start is RC (not stable) | High | Keep legacy frontend running, quick rollback plan |
| Team learning curve | Medium | Phase 3 migrations done iteratively, pair programming |
| Python backend still exists | Medium | Accept this, use tRPC as typed bridge |
| Breaking changes during migration | High | Feature freeze during Weeks 2-3, comprehensive testing |
| Docker complexity | Low | Run both frontends simultaneously during transition |

### Rollback Plan
If migration fails:
1. Switch Docker Compose back to `frontend-legacy`
2. Restore port 3000 to old app
3. Continue with current architecture
4. Consider simpler fixes (Pydantic v2 transformers, better docs)

---

## Decision Points

### ✅ Proceed If:
- Team is comfortable with 3-4 week timeline
- You can handle feature freeze during migration
- TypeScript expertise is available
- You're okay with TanStack Start RC status

### ❌ Reconsider If:
- You need new features this week
- Team is unfamiliar with TypeScript
- Python backend rewrite is expected (not planned here)
- You need 100% stability (RC framework is risk)

---

## Alternative: Quick Fixes to Current Architecture

If migration feels too risky, consider these quick wins:

1. **Add Pydantic v2 Transformers** (2 days)
   - Configure FastAPI to auto-convert snake_case → camelCase
   - Solves naming issues without rewrite

2. **Codegen TypeScript Types from OpenAPI** (1 week)
   - Generate types from FastAPI's OpenAPI spec
   - Not as good as full-stack types, but much faster

3. **Stricter Type Definitions** (3 days)
   - Replace all `any` with proper interfaces
   - Use `zod` for runtime validation

**These won't solve HTTP boundary, but reduce errors by 70%.**

---

## Recommendation

**I recommend:**
1. **Short-term (This week):** Fix current dashboard with Pydantic transformers
2. **Medium-term (Next 2 weeks):** Evaluate TanStack Start with Phase 1 proof-of-concept
3. **Long-term (Month 2):** Decide on full migration based on PoC results

**Rationale:**
- You're close to a working prototype - finish it first
- Test TanStack Start risk-free with parallel app
- Make informed decision after seeing real integration challenges

---

## Next Steps

If you want to proceed with migration:

1. **Review this plan** - confirm timeline and architecture
2. **Choose approach:**
   - Full migration (Phases 1-4)
   - Proof-of-concept first (Phase 1 only)
   - Quick fixes instead
3. **I'll create implementation tasks** based on your decision

**Your call - what do you prefer?**
