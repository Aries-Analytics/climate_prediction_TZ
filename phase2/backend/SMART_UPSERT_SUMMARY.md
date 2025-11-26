# Smart Upsert Implementation Summary

## Problem Solved
Previously, the data loader required manual intervention to clear old data before loading new data. This was:
- Error-prone (users might forget to clear)
- Time-consuming (extra steps)
- Risky (could accidentally keep bad data)

## Solution: Smart Upsert
The script now automatically handles existing data intelligently.

### How It Works

#### For Climate Data:
```python
# Check if record exists for this date and location
existing = db.query(ClimateData).filter(
    ClimateData.date == record_date,
    ClimateData.location_lat == TANZANIA_LAT,
    ClimateData.location_lon == TANZANIA_LON
).first()

if existing:
    # Update existing record
    existing.temperature_avg = new_value
    existing.rainfall_mm = new_value
    # ... update all fields
else:
    # Create new record
    db.add(new_climate_record)
```

#### For Trigger Events:
```python
# Check if record exists for this date, type, and location
existing = db.query(TriggerEvent).filter(
    TriggerEvent.date == record_date,
    TriggerEvent.trigger_type == trigger_type,
    TriggerEvent.location_lat == TANZANIA_LAT,
    TriggerEvent.location_lon == TANZANIA_LON
).first()

if existing:
    # Update existing record
    existing.confidence = new_confidence
    existing.severity = new_severity
    existing.payout_amount = new_payout
else:
    # Create new record
    db.add(new_trigger_event)
```

## Benefits

### 1. Automatic Correction
Run the script once, and it will:
- ✅ Fix all Kenya coordinates → Tanzania coordinates
- ✅ Update all payout calculations to correct values
- ✅ Update any other changed fields

### 2. Safe to Run Multiple Times
```bash
# First run: Loads all data
python load_sample_data.py
# Output: Added 500 new records, updated 0 existing records

# Second run: Updates existing data
python load_sample_data.py
# Output: Added 0 new records, updated 500 existing records

# Third run: No changes needed
python load_sample_data.py
# Output: Added 0 new records, updated 500 existing records
```

### 3. Incremental Updates
If your CSV files get new data:
- New records are added
- Existing records are updated
- Old records remain unchanged

### 4. No Manual Steps
Before:
1. Run script
2. See prompt "Do you want to clear and reload?"
3. Type "yes"
4. Wait for clearing
5. Wait for loading

After:
1. Run script
2. Done! ✅

## Technical Details

### Unique Key Identification

**Climate Data** is identified by:
- Date
- Location (lat/lon)

**Trigger Events** are identified by:
- Date
- Trigger Type
- Location (lat/lon)

This ensures we update the right records without duplicates.

### Performance
- Commits every 50-100 records for efficiency
- Uses SQLAlchemy's session management
- Minimal database queries (one check per record)

### Error Handling
- Transactions are rolled back on errors
- Partial updates are prevented
- Clear error messages for debugging

## Migration Path

### If You Have Old Data with Kenya Coordinates:

**Option 1: Automatic Fix (Recommended)**
```bash
python load_sample_data.py
```
The script will automatically update all records to Tanzania coordinates.

**Option 2: Manual Clear (If Needed)**
If you want to start completely fresh:
```bash
# Connect to database
docker-compose exec db psql -U climate_user -d climate_dashboard

# Clear tables
DELETE FROM trigger_events;
DELETE FROM climate_data;

# Exit and reload
\q
python load_sample_data.py
```

## Verification

After running the script, verify the updates:

```sql
-- Check Tanzania coordinates are applied
SELECT DISTINCT location_lat, location_lon FROM climate_data;
-- Should show: -6.369028, 34.888822

SELECT DISTINCT location_lat, location_lon FROM trigger_events;
-- Should show: -6.369028, 34.888822

-- Check payout amounts are realistic
SELECT trigger_type, AVG(payout_amount), MIN(payout_amount), MAX(payout_amount)
FROM trigger_events
WHERE payout_amount > 0
GROUP BY trigger_type;
-- Should show amounts in thousands, not single digits
```

## Future Enhancements

Potential improvements:
1. **Bulk upsert** using PostgreSQL's `ON CONFLICT` for better performance
2. **Change detection** to only update records that actually changed
3. **Audit logging** to track what was updated
4. **Dry-run mode** to preview changes before applying
5. **Configurable unique keys** for different deployment scenarios
