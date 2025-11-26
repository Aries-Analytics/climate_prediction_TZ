# Duplicate Records Cleanup Guide

## Problem: Why Do I Have 160 Events Instead of 80?

If you're seeing double the expected number of trigger events (or climate records), it's because you have **duplicate records** with different coordinates.

### What Happened:

1. **Old script** created records with Kenya coordinates (-1.2921, 36.8219)
2. **New script** creates records with Tanzania coordinates (-6.369028, 34.888822)
3. The upsert logic sees these as **different records** (different locations)
4. Result: You have both sets in the database!

### Example:
```
Old Record: Date=2020-01-01, Type=drought, Location=Kenya coords
New Record: Date=2020-01-01, Type=drought, Location=Tanzania coords
```
These are treated as separate records, even though they represent the same event.

## Solution: Run the Cleanup Script

### Step 1: Check for Duplicates

```bash
cd backend
python cleanup_old_coordinates.py
```

The script will show you:
```
Current database status:

Old Kenya coordinates:
  - Climate records: 500
  - Trigger events: 80

New Tanzania coordinates:
  - Climate records: 500
  - Trigger events: 80
```

### Step 2: Confirm Deletion

When prompted:
```
Do you want to delete the old Kenya records? (yes/no):
```

Type `yes` to remove the duplicates.

### Step 3: Verify

After cleanup:
```
Cleanup Complete!
Remaining climate records: 500
Remaining trigger events: 80

✓ All records now use correct Tanzania coordinates!
```

## Prevention: The Script Now Warns You

The updated `load_sample_data.py` now **detects** old Kenya coordinates and warns you:

```
⚠️  WARNING: Found old records with Kenya coordinates:
  - Climate: 500
  - Triggers: 80

These are duplicates! Run 'python cleanup_old_coordinates.py' first
to remove them before loading new data.

Continue anyway? (yes/no):
```

## Manual Cleanup (Alternative)

If you prefer to clean up manually using SQL:

```bash
# Connect to database
docker-compose exec db psql -U climate_user -d climate_dashboard

# Check for duplicates
SELECT location_lat, location_lon, COUNT(*) 
FROM trigger_events 
GROUP BY location_lat, location_lon;

# Delete old Kenya coordinates
DELETE FROM climate_data 
WHERE location_lat = -1.2921 AND location_lon = 36.8219;

DELETE FROM trigger_events 
WHERE location_lat = -1.2921 AND location_lon = 36.8219;

# Verify
SELECT COUNT(*) FROM climate_data;
SELECT COUNT(*) FROM trigger_events;

\q
```

## Why This Happened

The upsert logic identifies records by:
- **Date**
- **Type** (for triggers)
- **Location** (lat/lon)

When coordinates changed from Kenya to Tanzania, the script couldn't match old records to new ones, so it created new records instead of updating.

## Future Prevention

Going forward, this won't happen again because:

1. ✅ Script now uses Tanzania coordinates consistently
2. ✅ Script warns if old coordinates are detected
3. ✅ Cleanup script is available for one-time fix
4. ✅ Upsert logic will update existing Tanzania records

## FAQ

### Q: Will I lose data if I delete old records?
**A:** No! The new records contain the same data, just with correct Tanzania coordinates and updated payout calculations.

### Q: Can I just keep both sets?
**A:** Not recommended. You'll have:
- Duplicate events in dashboards
- Incorrect analytics (double counting)
- Confusion about which data is correct

### Q: What if I run the data loader again?
**A:** After cleanup, the script will:
- Find existing Tanzania records
- Update them (not create duplicates)
- Work correctly going forward

### Q: How do I know which coordinates are correct?
**A:** Tanzania coordinates are correct:
- Latitude: -6.369028
- Longitude: 34.888822

Kenya coordinates are incorrect (old):
- Latitude: -1.2921
- Longitude: 36.8219

## Summary

1. **Problem**: Coordinate change created duplicates
2. **Detection**: Script now warns you
3. **Solution**: Run `cleanup_old_coordinates.py`
4. **Prevention**: Won't happen again with Tanzania coords
