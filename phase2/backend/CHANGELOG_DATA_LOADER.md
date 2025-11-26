# Data Loader Changelog

## Version 2.0 - Tanzania Update (2024)

### Critical Fixes

#### 1. Geographic Location Correction
**Issue**: Script was using Kenya coordinates instead of Tanzania
**Fix**: Updated all location coordinates to Tanzania center
- Old: Latitude -1.2921, Longitude 36.8219 (Kenya)
- New: Latitude -6.369028, Longitude 34.888822 (Tanzania)

**Files Changed**:
- `load_sample_data.py` - Lines 40, 96

#### 2. Trigger Type Handling
**Issue**: Script couldn't handle both "Crop Failure" and "crop_failure" formats
**Fix**: Added support for both capitalized and lowercase formats
- Now accepts: ['Drought', 'Flood', 'Crop Failure', 'drought', 'flood', 'crop_failure']
- Normalizes all to lowercase with underscores for database storage

**Files Changed**:
- `load_sample_data.py` - Line 73

#### 3. Payout Calculation Clarity
**Issue**: Payout calculation logic was unclear and used generic values
**Fix**: 
- Added clear comments explaining Tanzania-specific payout amounts
- Documented the 30% severity threshold
- Made base payouts more realistic for East African context

**Files Changed**:
- `load_sample_data.py` - Lines 85-95

### Improvements

#### 1. Code Documentation
- Added comprehensive docstring explaining Tanzania focus
- Added reference coordinates in header
- Added inline comments for clarity

#### 2. Constants
- Extracted Tanzania coordinates as named constants (TANZANIA_LAT, TANZANIA_LON)
- Makes future updates easier and more maintainable

#### 3. Error Handling
- Improved confidence parsing with try/except
- Better handling of missing or malformed data

### New Documentation

#### 1. DATA_LOADING_GUIDE.md
Comprehensive guide covering:
- How to run the data loader
- What data gets loaded
- Tanzania-specific configuration
- Troubleshooting common issues
- Maintenance procedures
- Verification steps

### Migration Notes

If you have existing data loaded with Kenya coordinates:
1. Clear the database: Answer "yes" when prompted by the script
2. Reload with the updated script
3. Verify the new Tanzania coordinates in the dashboard

### Testing Checklist

After running the updated script, verify:
- [ ] Climate data shows Tanzania coordinates (-6.369028, 34.888822)
- [ ] Trigger events show Tanzania coordinates
- [ ] All three trigger types load correctly (drought, flood, crop_failure)
- [ ] Payout amounts are realistic (not 0-7,600 range)
- [ ] Dashboard displays data correctly
- [ ] No errors in console or logs

### Smart Upsert Implementation (Latest)

**Issue**: Manual clearing of data was required every time the script ran
**Fix**: Implemented intelligent upsert (update or insert) logic

**How it works**:
- Checks if each record already exists (by date, type, and location)
- Updates existing records with new values
- Inserts new records that don't exist
- No manual intervention required!

**Benefits**:
- Run the script multiple times safely
- Automatically fixes old Kenya coordinates to Tanzania
- Automatically updates payout calculations
- No data loss - only updates what's needed

**Files Changed**:
- `load_sample_data.py` - Complete rewrite of load functions
- `DATA_LOADING_GUIDE.md` - Updated documentation

### Future Improvements

Potential enhancements for future versions:
1. Support for multiple regions within Tanzania
2. Configurable payout amounts via config file
3. Validation of CSV column names before loading
4. Progress bar for large datasets
5. Dry-run mode to preview changes
6. Transaction rollback on partial failures
