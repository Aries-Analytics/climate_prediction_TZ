# Data Loading Guide

## Overview
This guide explains how to properly load sample data into the Tanzania Climate Prediction Dashboard database.

## Prerequisites
1. Ensure the master dataset exists at: `../outputs/processed/master_dataset.csv`
2. Ensure the triggers CSV exists at: `../outputs/business_reports/insurance_triggers_detailed.csv`
3. Database must be running (via Docker Compose)

## Running the Data Loader

### From the backend directory:
```bash
cd backend
python load_sample_data.py
```

### From Docker:
```bash
docker-compose -f docker-compose.dev.yml exec backend python load_sample_data.py
```

## What Gets Loaded

### 1. Climate Data
- **Source**: `master_dataset.csv`
- **Sampling**: Every 10th row (to avoid overloading)
- **Location**: Tanzania center coordinates (-6.369028, 34.888822)
- **Fields**:
  - Date
  - Temperature (temperature_2m_mean)
  - Rainfall (precipitation_sum)
  - NDVI (ndvi_mean)
  - ENSO Index (nino34)
  - IOD Index (dmi)

### 2. Trigger Events
- **Source**: `insurance_triggers_detailed.csv`
- **Types**: Drought, Flood, Crop Failure
- **Location**: Tanzania center coordinates (-6.369028, 34.888822)
- **Payout Calculation**:
  - Base payouts (USD):
    - Drought: $25,000
    - Flood: $35,000
    - Crop Failure: $20,000
  - Payout = Base × Severity (only if severity > 30%)

## Important Notes

### Tanzania-Specific Configuration
The script is configured for **Tanzania**, not Kenya. Coordinates are set to Tanzania's approximate center:
- Latitude: -6.369028
- Longitude: 34.888822

### Data Validation
The script handles:
- Duplicate trigger events (keeps first occurrence per date/type)
- Missing confidence values (defaults to 0.0)
- Both formats of trigger types (e.g., "Crop Failure" and "crop_failure")

### Smart Upsert Behavior
The script now uses **smart upsert** logic:
1. Shows current record counts
2. Automatically updates existing records with new data
3. Adds new records that don't exist yet
4. **No manual clearing required!**

This means you can run the script multiple times safely - it will:
- Update Tanzania coordinates on old Kenya data automatically
- Update payout calculations to correct values
- Add any new records from updated CSV files

## Troubleshooting

### Error: "File not found"
- Ensure you're running from the correct directory
- Check that the CSV files exist at the specified paths
- Verify the relative paths are correct

### Error: "Database connection failed"
- Ensure the database container is running
- Check database credentials in `.env` file
- Verify the database service is healthy: `docker-compose ps`

### Error: "Column not found"
- The master dataset columns may have changed
- Check the actual column names in your CSV files
- Update the script's column mappings if needed

## Maintenance

### Updating Coordinates
If you need to change the location coordinates, update both functions:
1. `load_climate_data()` - TANZANIA_LAT and TANZANIA_LON
2. `load_trigger_events()` - TANZANIA_LAT and TANZANIA_LON

Then simply run the script - it will automatically update all existing records with the new coordinates!

### Updating Payout Amounts
To adjust payout calculations, modify the `base_payouts` dictionary in `load_trigger_events()`:
```python
base_payouts = {
    'drought': 25000,
    'flood': 35000,
    'crop_failure': 20000
}
```

### Adding New Data Sources
To add new data sources:
1. Create a new function (e.g., `load_predictions()`)
2. Follow the same pattern as existing functions
3. Add the function call to `main()`
4. Update this documentation

## Verification

After loading data, verify in the dashboard:
1. Navigate to http://localhost:3000
2. Check the Executive Dashboard for KPIs
3. Check the Trigger Events Dashboard for event data
4. Check the Climate Insights Dashboard for climate data

You can also verify directly in the database:
```bash
docker-compose exec db psql -U climate_user -d climate_dashboard -c "SELECT COUNT(*) FROM climate_data;"
docker-compose exec db psql -U climate_user -d climate_dashboard -c "SELECT COUNT(*) FROM trigger_events;"
```
