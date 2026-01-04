# Dynamic vs Hardcoded: Year Selection Implementation

## Question
Should the year dropdown in the Executive Dashboard be hardcoded or dynamic?

## Answer: Dynamic is Better

### Implementation
We implemented a **dynamic approach** that fetches available years from the database.

### Why Dynamic?

#### 1. **Future-Proof** ✓
- When you add 2026 data, the dropdown automatically includes it
- No code changes needed when data grows
- Works for any time range

#### 2. **Data-Driven** ✓
- Shows only years that actually have data
- Prevents users from selecting years with no data
- Accurate representation of what's available

#### 3. **Low Maintenance** ✓
- One-time implementation
- No annual code updates
- Fewer deployments

#### 4. **Better UX** ✓
- Users see exactly what's available
- No confusion about missing data
- Automatically adapts to data changes

### How It Works

**Backend** (`/api/dashboard/years`):
```python
def get_available_years(db: Session) -> List[int]:
    """Get list of years that have data in the database"""
    years = db.query(
        extract('year', TriggerEvent.date).label('year')
    ).distinct().order_by('year').all()
    
    return [int(year[0]) for year in years]
```

**Frontend**:
```typescript
// Fetch available years on mount
useEffect(() => {
  fetchAvailableYears()
}, [])

const fetchAvailableYears = async () => {
  const response = await axios.get(`${API_BASE_URL}/dashboard/years`)
  const years = response.data.years
  setYearOptions(years.sort((a, b) => b - a)) // Descending
  setSelectedYear(Math.max(...years)) // Default to most recent
}
```

### Fallback Strategy

We include a fallback to hardcoded years if the API fails:
```typescript
catch (err) {
  // Fallback to hardcoded range if API fails
  const fallbackYears = Array.from({ length: 16 }, (_, i) => 2025 - i)
  setYearOptions(fallbackYears)
  setSelectedYear(2025)
}
```

This ensures the dashboard always works, even if there's a temporary API issue.

### Performance

- **Caching**: Results cached for 1 hour (years don't change often)
- **Single Query**: One simple database query
- **Minimal Overhead**: Negligible performance impact

### When Hardcoded Might Be OK

Hardcoded values are acceptable when:
- The range is truly fixed (e.g., "Select month: Jan-Dec")
- It's a configuration constant (e.g., "Max file size: 10MB")
- The values never change (e.g., "Select country code")

But for **data-dependent values like years**, dynamic is always better.

## Conclusion

**Dynamic approach wins** because:
1. Zero maintenance when data grows
2. Always accurate
3. Better user experience
4. Minimal performance cost
5. Future-proof

The small upfront cost of implementing the API endpoint pays off immediately and continues to provide value as the system grows.
