# Performance Optimization Guide

## Overview

This guide explains the performance optimizations implemented in the Tanzania Climate Prediction API and how to use them effectively.

---

## Caching System

### Overview

The API implements a two-tier caching system:
1. **Redis Cache** (Primary): Fast, distributed caching
2. **In-Memory Cache** (Fallback): Automatic fallback when Redis is unavailable

### Configuration

**Environment Variables** (`.env`):
```env
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=300
CACHE_ENABLED=true
```

### Using the Cache

#### Automatic Caching (Decorator)

```python
from app.core.cache import cached

@cached(ttl=300, key_prefix="my_function")
async def my_expensive_function(param1, param2):
    # Expensive operation
    result = perform_calculation(param1, param2)
    return result
```

#### Manual Caching

```python
from app.core.cache import cache_manager

# Set cache
await cache_manager.set("my_key", {"data": "value"}, ttl=300)

# Get cache
data = await cache_manager.get("my_key")

# Delete cache
await cache_manager.delete("my_key")

# Clear pattern
await cache_manager.clear_pattern("dashboard:*")
```

### Cache Invalidation

**When to Invalidate**:
- After data updates (POST, PUT, DELETE operations)
- After configuration changes
- On scheduled intervals

**Example**:
```python
from app.core.cache import invalidate_cache_pattern

# Invalidate all dashboard caches
await invalidate_cache_pattern("dashboard:*")

# Invalidate specific cache
await cache_manager.delete("dashboard:executive")
```

### Monitoring Cache Performance

```python
# Get cache statistics
stats = await cache_manager.get_connection_stats()
print(f"Cache enabled: {stats['redis_connected']}")
```

**Redis CLI**:
```bash
# Connect to Redis
redis-cli

# Get cache statistics
INFO stats

# Monitor cache operations
MONITOR

# Check memory usage
INFO memory

# List all keys
KEYS *

# Get cache hit rate
INFO stats | grep hit_rate
```

---

## Database Optimization

### Indexes

The following indexes have been added for optimal query performance:

#### TriggerEvent Table

```sql
-- Composite index for date and type queries
CREATE INDEX idx_trigger_date_type ON trigger_events(date, trigger_type);

-- Index for time-based queries
CREATE INDEX idx_trigger_created_at ON trigger_events(created_at);

-- Index for location-based queries
CREATE INDEX idx_trigger_location ON trigger_events(location_lat, location_lon);
```

#### ClimateData Table

```sql
-- Composite index for date and location queries
CREATE INDEX idx_climate_date_location ON climate_data(date, location_lat, location_lon);

-- Index for time-based queries
CREATE INDEX idx_climate_created_at ON climate_data(created_at);
```

### Query Optimization Tips

#### 1. Use Indexed Columns in WHERE Clauses

**Good**:
```python
# Uses idx_trigger_date_type index
triggers = db.query(TriggerEvent).filter(
    TriggerEvent.date >= start_date,
    TriggerEvent.trigger_type == "drought"
).all()
```

**Bad**:
```python
# No index on payout_amount
triggers = db.query(TriggerEvent).filter(
    TriggerEvent.payout_amount > 1000
).all()
```

#### 2. Use Pagination

**Good**:
```python
# Limit results
triggers = db.query(TriggerEvent).limit(50).offset(0).all()
```

**Bad**:
```python
# Loads all records
triggers = db.query(TriggerEvent).all()
```

#### 3. Use Eager Loading

**Good**:
```python
from sqlalchemy.orm import selectinload

# Load related data in one query
triggers = db.query(TriggerEvent).options(
    selectinload(TriggerEvent.climate_data)
).all()
```

**Bad**:
```python
# N+1 query problem
triggers = db.query(TriggerEvent).all()
for trigger in triggers:
    climate = trigger.climate_data  # Separate query for each
```

### Monitoring Database Performance

```sql
-- Find slow queries
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '1 second'
ORDER BY duration DESC;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Find unused indexes
SELECT schemaname, tablename, indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND indexname NOT LIKE 'pg_toast%';

-- Table sizes
SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Analyze query plan
EXPLAIN ANALYZE
SELECT * FROM trigger_events
WHERE date >= '2024-01-01' AND trigger_type = 'drought';
```

---

## Chart Data Optimization

### Overview

Large datasets are automatically optimized for chart rendering using the LTTB (Largest Triangle Three Buckets) algorithm.

### API Usage

```bash
# Automatic optimization when data exceeds max_points
GET /api/climate/timeseries?variable=temperature_avg&max_points=1000
```

**Response**:
```json
{
  "variable": "temperature_avg",
  "data": [...],  // Optimized to 1000 points
  "optimized": true,
  "original_count": 5000
}
```

### Manual Optimization

```python
from app.utils.data_optimization import optimize_for_chart

# Optimize data for chart rendering
data = [{"date": "2024-01-01", "value": 28.5}, ...]
optimized_data = optimize_for_chart(data, max_points=1000)
```

### Downsampling Options

```python
from app.utils.data_optimization import downsample_timeseries

# Downsample with specific fields
downsampled = downsample_timeseries(
    data=raw_data,
    max_points=1000,
    date_field="date",
    value_fields=["temperature", "rainfall"]
)
```

### Time-Based Aggregation

```python
from app.utils.data_optimization import aggregate_by_time_window

# Aggregate by day
daily_data = aggregate_by_time_window(
    data=raw_data,
    window="day",
    aggregation="mean"
)

# Aggregate by week
weekly_data = aggregate_by_time_window(
    data=raw_data,
    window="week",
    aggregation="sum"
)

# Aggregate by month
monthly_data = aggregate_by_time_window(
    data=raw_data,
    window="month",
    aggregation="max"
)
```

---

## Performance Best Practices

### API Development

1. **Use Caching for Expensive Operations**
   ```python
   @cached(ttl=600)  # Cache for 10 minutes
   async def expensive_calculation():
       # Complex calculation
       return result
   ```

2. **Implement Pagination**
   ```python
   @router.get("/items")
   def get_items(page: int = 1, page_size: int = 50):
       offset = (page - 1) * page_size
       items = db.query(Item).limit(page_size).offset(offset).all()
       return items
   ```

3. **Use Database Indexes**
   - Add indexes to frequently queried columns
   - Use composite indexes for multi-column queries
   - Monitor index usage and remove unused indexes

4. **Optimize Data Transfer**
   ```python
   # Return only needed fields
   @router.get("/items")
   def get_items():
       items = db.query(Item.id, Item.name).all()  # Not Item.*
       return items
   ```

5. **Use Async Operations**
   ```python
   # Use async for I/O operations
   @router.get("/data")
   async def get_data():
       data = await fetch_from_external_api()
       return data
   ```

### Frontend Development

1. **Lazy Load Components**
   ```javascript
   const HeavyComponent = lazy(() => import('./HeavyComponent'));
   ```

2. **Implement Virtual Scrolling**
   - Use for large tables
   - Render only visible rows

3. **Optimize Chart Rendering**
   - Use `max_points` parameter
   - Implement chart throttling
   - Use canvas instead of SVG for large datasets

4. **Cache API Responses**
   ```javascript
   // Use React Query or SWR for client-side caching
   const { data } = useQuery('dashboard', fetchDashboard, {
     staleTime: 5 * 60 * 1000  // 5 minutes
   });
   ```

---

## Performance Monitoring

### Key Metrics to Monitor

1. **API Response Time**
   - Target: < 500ms (95th percentile)
   - Monitor: `/health` endpoint

2. **Database Query Time**
   - Target: < 200ms per query
   - Monitor: PostgreSQL slow query log

3. **Cache Hit Rate**
   - Target: > 80%
   - Monitor: Redis INFO stats

4. **Memory Usage**
   - Target: < 80% of available RAM
   - Monitor: System metrics

5. **CPU Usage**
   - Target: < 70% average
   - Monitor: System metrics

### Monitoring Tools

**Application Performance**:
```python
# Add timing middleware
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

**Database Performance**:
```sql
-- Enable slow query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
SELECT pg_reload_conf();
```

**Redis Performance**:
```bash
# Monitor Redis operations
redis-cli --latency
redis-cli --stat
```

---

## Troubleshooting Performance Issues

### Slow API Responses

**Diagnosis**:
1. Check cache hit rate
2. Review database query logs
3. Check for N+1 query problems
4. Monitor network latency

**Solutions**:
- Increase cache TTL
- Add database indexes
- Use eager loading
- Optimize queries

### High Memory Usage

**Diagnosis**:
1. Check for memory leaks
2. Review cache size
3. Monitor large query results

**Solutions**:
- Implement pagination
- Reduce cache size
- Use streaming for large datasets
- Implement data cleanup

### Slow Chart Rendering

**Diagnosis**:
1. Check data point count
2. Review browser console
3. Monitor network transfer size

**Solutions**:
- Use `max_points` parameter
- Implement data downsampling
- Use canvas rendering
- Implement progressive loading

### Database Connection Issues

**Diagnosis**:
1. Check connection pool size
2. Review active connections
3. Monitor connection timeouts

**Solutions**:
- Increase pool size
- Implement connection pooling
- Add connection timeout handling
- Use connection retry logic

---

## Performance Testing

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test API endpoint
ab -n 1000 -c 10 http://localhost:8000/api/dashboard/executive

# Test with authentication
ab -n 1000 -c 10 -H "Authorization: Bearer TOKEN" http://localhost:8000/api/triggers
```

### Database Performance Testing

```sql
-- Test query performance
EXPLAIN ANALYZE
SELECT * FROM trigger_events
WHERE date >= '2024-01-01'
AND trigger_type = 'drought'
ORDER BY date DESC
LIMIT 50;
```

### Cache Performance Testing

```python
import time
import asyncio
from app.core.cache import cache_manager

async def test_cache_performance():
    # Test cache write
    start = time.time()
    await cache_manager.set("test_key", {"data": "value"})
    write_time = time.time() - start
    
    # Test cache read
    start = time.time()
    data = await cache_manager.get("test_key")
    read_time = time.time() - start
    
    print(f"Write time: {write_time*1000:.2f}ms")
    print(f"Read time: {read_time*1000:.2f}ms")

asyncio.run(test_cache_performance())
```

---

## Optimization Checklist

### Before Deployment

- [ ] Enable caching for frequently accessed endpoints
- [ ] Add database indexes for common queries
- [ ] Implement pagination for large datasets
- [ ] Optimize chart data with downsampling
- [ ] Enable compression for API responses
- [ ] Configure connection pooling
- [ ] Set up monitoring and alerting
- [ ] Test under expected load
- [ ] Review and optimize slow queries
- [ ] Implement rate limiting

### Regular Maintenance

- [ ] Monitor cache hit rates weekly
- [ ] Review slow query logs weekly
- [ ] Analyze database index usage monthly
- [ ] Update dependencies monthly
- [ ] Performance audit quarterly
- [ ] Load testing quarterly

---

## Additional Resources

- **FastAPI Performance**: https://fastapi.tiangolo.com/deployment/
- **PostgreSQL Performance**: https://wiki.postgresql.org/wiki/Performance_Optimization
- **Redis Best Practices**: https://redis.io/topics/optimization
- **React Performance**: https://react.dev/learn/render-and-commit

---

**Last Updated**: November 21, 2025  
**Version**: 1.0
