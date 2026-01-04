# Geographic Map Choropleth Rendering - Debugging Guide

**Date**: 2026-01-03  
**Component**: `frontend/src/components/GeographicMap.tsx`  
**Issue**: Choropleth layer not displaying colors, all regions render gray

---

## Problem Summary

The geographic map component displays trigger events across Tanzania using:
1. **Choropleth layer** - Regional polygons colored by total payout
2. **Circle markers** - City-specific event indicators

**Observed Behavior**:
- All regional polygons render as gray (`rgba(200, 200, 200, 0.2)`)
- Circle markers render gray instead of trigger-type colors
- Tooltips show $0 payout and 0 triggers for all regions
- Console logs show: `Events grouped by region: []`

---

## Root Cause Analysis

### Issue 1: GeoJSON Structure Destruction ❌

**Initial Implementation** (WRONG):
```typescript
const regionalData = useMemo(() => {
  return tanzaniaRegions.features.map(feature => {
    return {
      name: regionName,
      bounds: feature.geometry.coordinates[0],  // ❌ Destroyed geometry!
      totalPayout,
      triggerCount
    };
  });
}, [events]);
```

**Problem**:
- Created custom objects instead of preserving GeoJSON format
- `bounds: coordinates[0]` only works for Polygon, fails silently for MultiPolygon
- Leaflet/react-leaflet require valid GeoJSON structure for choropleth rendering
- Breaking GeoJSON spec → choropleth cannot render

**Scientific Explanation**:
- Tanzania administrative regions use **both** Polygon and MultiPolygon geometries
- Polygon: `feature.geometry.coordinates = [[[lon, lat], ...]]`
- MultiPolygon: `feature.geometry.coordinates = [[[[lon, lat], ...]], ...]`
- Extracting only `coordinates[0]` fails for MultiPolygon regions

---

### Issue 2: City vs Region Name Mismatch ❌

**Initial Approach**:
```typescript
const eventsByCity = new Map();
events.forEach(e => {
  const cityName = getCityName(lat, lon);  // Returns "Arusha"
  eventsByCity.set(cityName, ...);
});

// Later...
const regionName = feature.properties.name;  // "Arusha"
const regionTriggers = eventsByCity.get(regionName);  // Should work!
```

**Problem**:
- Assumed city names match region names exactly
- In Tanzania, our 6 cities **DO** match region names:
  - Arusha city → Arusha region ✅
  - Dar es Salaam city → Dar es Salaam region ✅
  - etc.
- **But** this wasn't the issue - the real problem was coordinate parsing!

---

### Issue 3: Coordinate Type Mismatch (ACTUAL CAUSE) ❌

**Current Code**:
```typescript
const enrichedRegions = useMemo(() => {
  const eventsByRegion = new Map();
  
  events.forEach(e => {
    const lat = e.locationLat;  // ❌ From API: STRING "number"
    const lon = e.locationLon;  // ❌ From API: STRING "-6.7924"
    
    if (typeof lat === 'number' && !isNaN(lat) && 
        typeof lon === 'number' && !isNaN(lon)) {
      // ❌ NEVER EXECUTES - lat/lon are strings!
      const cityName = getCityName(lat, lon);
      eventsByRegion.set(cityName, ...);
    }
  });
  // Result: eventsByRegion is EMPTY
}, [events]);
```

**Problem**:
- API returns PostgreSQL `Decimal` types as **strings** (e.g., `"number"-6.7924"`)
- Type check `typeof lat === 'number'` fails
- No events pass validation
- `eventsByRegion` map stays empty
- All regions get 0 triggers, $0 payout

**Evidence**:
```
Console: Events grouped by region: []
Console: Region Arusha: 0 triggers, $0.00 payout
Console: Region Dar es Salaam: 0 triggers, $0.00 payout
```

---

## Solution Implementation

### Fix 1: Preserve GeoJSON Structure ✅

**Correct Implementation**:
```typescript
const enrichedRegions = useMemo(() => {
  // ... grouping logic ...
  
  return {
    ...tanzaniaRegions,  // Preserve FeatureCollection
    type: 'FeatureCollection' as const,
    features: tanzaniaRegions.features.map(feature => {
      const regionName = feature.properties.name;
      const regionEvents = eventsByRegion.get(regionName) || [];
      const totalPayout = /* calculate */;
      
      return {
        ...feature,  // ✅ Preserve complete geometry
        properties: {
          ...feature.properties,  // ✅ Keep existing props
          totalPayout,  // ✅ Add calculated data
          triggerCount: regionEvents.length
        }
      };
    })
  };
}, [events]);
```

**Benefits**:
- Maintains valid GeoJSON FeatureCollection
- Preserves Polygon/MultiPolygon geometries
- Choropleth libraries can render correctly
- Properties enriched, not replaced

---

### Fix 2: Parse String Coordinates (PENDING) ⚠️

**Required Fix**:
```typescript
const enrichedRegions = useMemo(() => {
  const eventsByRegion = new Map();
  
  events.forEach(e => {
    const latRaw = e.locationLat;
    const lonRaw = e.locationLon;
    
    // ✅ Parse strings to numbers FIRST
    const lat = typeof latRaw === 'string' ? parseFloat(latRaw) : latRaw;
    const lon = typeof lonRaw === 'string' ? parseFloat(lonRaw) : lonRaw;
    
    // ✅ Now type check works
    if (typeof lat === 'number' && !isNaN(lat) && 
        typeof lon === 'number' && !isNaN(lon)) {
      const cityName = getCityName(lat, lon);
      // ... rest of logic
    }
  });
}, [events]);
```

**Why This Works**:
- Converts string coordinates to numbers before validation
- `parseFloat("-6.7924")` → `-6.7924` (number)
- Type check passes
- Events get grouped correctly
- Regions get colored based on actual data

---

## Data Flow Architecture

```
API Response
└─> events[].locationLat: "number"-3.3869" (STRING)
└─> events[].locationLon: "36.6830" (STRING)
     │
     ├─> parseFloat() ✅
     │
     └─> getCityName(-3.3869, 36.6830)
         └─> Returns: "Arusha"
              │
              └─> eventsByRegion.set("Arusha", [...events])
                   │
                   └─> GeoJSON enrichment
                       └─> feature.properties.totalPayout = $45,320
                            │
                            └─> getHeatmapColor(45320)
                                 └─> Returns: "rgba(255, 255, 153, 0.5)"
                                      │
                                      └─> Polygon renders YELLOW ✅
```

---

## Choropleth Rendering Requirements

### Valid GeoJSON Structure
```typescript
{
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      geometry: {
        type: "Polygon" | "MultiPolygon",
        coordinates: [...] // Must preserve original
      },
      properties: {
        name: "Arusha",
        totalPayout: 45320,  // Custom data
        triggerCount: 89
      }
    }
  ]
}
```

### Invalid Structure (DO NOT USE)
```typescript
[
  {
    name: "Arusha",
    bounds: [[...]], // ❌ Not GeoJSON
    totalPayout: 45320
  }
]
```

---

## Color Scale Implementation

```typescript
const getHeatmapColor = (payout: number): string => {
  if (payout === 0) return 'rgba(200, 200, 200, 0.2)';      // Gray
  if (payout < 10000) return 'rgba(173, 216, 230, 0.4)';    // Light blue
  if (payout < 50000) return 'rgba(255, 255, 153, 0.5)';    // Yellow
  if (payout < 100000) return 'rgba(255, 165, 0, 0.5)';     // Orange
  return 'rgba(220, 20, 60, 0.6)';                          // Red
};
```

**Ranges**:
- **$0**: No risk (gray)
- **$1-9,999**: Low risk (light blue)
- **$10k-49k**: Medium risk (yellow)
- **$50k-99k**: High risk (orange)
- **$100k+**: Extreme risk (red)

---

## City-to-Region Mapping

Our 6-city dataset has city names that exactly match administrative region names:

| City Coordinates | City Name | Region Name | Match |
|-----------------|-----------|-------------|-------|
| -3.3869, 36.6830 | Arusha | Arusha | ✅ |
| -6.7924, 39.2083 | Dar es Salaam | Dar es Salaam | ✅ |
| -6.1630, 35.7516 | Dodoma | Dodoma | ✅ |
| -8.9094, 33.4606 | Mbeya | Mbeya | ✅ |
| -2.5164, 32.9175 | Mwanza | Mwanza | ✅ |
| -6.8211, 37.6595 | Morogoro | Morogoro | ✅ |

**Tolerance**: `0.01°` (~1km) for coordinate matching

---

## Debugging Checklist

When choropleth doesn't render colors:

1. **Check GeoJSON structure** ✅
   - [ ] Returning FeatureCollection?
   - [ ] Preserving original geometry?
   - [ ] Not extracting coordinates manually?

2. **Check data parsing** ⚠️ CURRENT ISSUE
   - [ ] Parsing string coordinates to numbers?
   - [ ] Type validation passing?
   - [ ] Events being grouped?

3. **Check name matching**
   - [ ] City names = Region names?
   - [ ] Exact string match (case-sensitive)?

4. **Check console logs**
   - [ ] "Events grouped by region" shows data?
   - [ ] Region logs show non-zero payouts?

5. **Check color function**
   - [ ] Payout values > 0?
   - [ ] Returning valid RGBA strings?

---

## Testing Commands

```bash
# Check API response format
curl http://localhost:8000/api/triggers | jq '.[0] | {locationLat, locationLon}'

# Check if coordinates are strings
# Expected: "locationLat": "-3.3869" (string)

# Rebuild frontend
docker-compose -f docker-compose.dev.yml restart frontend

# Check browser console
# Look for: "Events grouped by region: [...]"
# Should show: Arusha: 86 events, Dar es Salaam: 95 events, etc.
```

---

## Current Status

- **GeoJSON Structure**: ✅ FIXED
- **MultiPolygon Handling**: ✅ FIXED
- **Coordinate Parsing**: ✅ FIXED (Added `parseFloat`)
- **Color Rendering**: ✅ FIXED
- **Deployment Sync**: ✅ FIXED (Requires container restart)

**Final Resolution**:
1.  **Code Fix**: Added strict `parseFloat(latRaw)` and `parseFloat(lonRaw)` in `enrichedRegions` to handle API string responses.
2.  **Environment Fix**: Restarted frontend container (`docker-compose restart frontend`) to resolve Docker volume sync latency where browser was serving stale code.

**Outcome**: Map correctly displays colored regions (choropleth) based on payout density and colored markers for trigger types.

---

## References

- **GeoJSON Spec**: https://geojson.org/
- **react-leaflet Polygon**: https://react-leaflet.js.org/docs/api-components/#polygon
- **Tanzania Regions GeoJSON**: `frontend/src/assets/tanzania-regions.json`
- **Component**: `frontend/src/components/GeographicMap.tsx`
