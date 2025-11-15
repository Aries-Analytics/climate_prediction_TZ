# Design Document

## Overview

This design addresses the issue where the CHIRPS ingestion module fails to fetch real data from the UCSB Climate Hazards Center API due to an incorrect URL structure. Research has revealed that the correct URL pattern uses a `byYear/` subdirectory and `.monthly.nc` file naming convention instead of `.months_p05.nc`. The solution involves updating the URL construction logic, adding URL validation before download, improving error handling, and implementing data authenticity verification.

**Root Cause:** The current implementation uses the URL pattern:
```
https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/netcdf/chirps-v2.0.{year}.months_p05.nc
```

The correct URL pattern is:
```
https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/netcdf/byYear/chirps-v2.0.{year}.monthly.nc
```

**Key Differences:**
- Missing `byYear/` subdirectory in path
- Incorrect filename suffix: `months_p05.nc` → `monthly.nc`

## Architecture

### Current Flow
```
fetch_chirps_data()
  ├─> Construct URL (INCORRECT)
  ├─> Download NetCDF file (FAILS with 404)
  ├─> Fall back to cached data
  └─> Generate synthetic sample data
```

### Proposed Flow
```
fetch_chirps_data()
  ├─> Construct URL (CORRECTED)
  ├─> Validate URL exists (HEAD request)
  ├─> Download NetCDF file (SUCCESS)
  ├─> Process and extract Tanzania region
  ├─> Validate data authenticity
  └─> Save real CHIRPS data
```

### Components Modified

1. **URL Construction Logic** (`fetch_chirps_data` function)
   - Update base URL to include `byYear/` subdirectory
   - Change filename pattern from `.months_p05.nc` to `.monthly.nc`

2. **URL Validation** (new helper function)
   - Add pre-download HEAD request to verify file exists
   - Log validation results for debugging

3. **Error Handling** (enhanced)
   - Distinguish between network errors, HTTP errors, and processing errors
   - Provide actionable error messages with specific URLs
   - Remove automatic fallback to synthetic data when API is accessible

4. **Data Authenticity Verification** (new helper function)
   - Validate NetCDF structure and dimensions
   - Check rainfall value ranges against Tanzania climatology
   - Calculate and log data statistics

## Components and Interfaces

### 1. URL Construction

**Function:** `_construct_chirps_url(year: int) -> str`

**Purpose:** Build the correct CHIRPS data URL for a given year

**Implementation:**
```python
def _construct_chirps_url(year: int) -> str:
    """
    Construct the correct CHIRPS NetCDF URL for a given year.
    
    Parameters
    ----------
    year : int
        Year for which to fetch data
        
    Returns
    -------
    str
        Complete URL to CHIRPS NetCDF file
    """
    base_url = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/netcdf/byYear"
    filename = f"chirps-v2.0.{year}.monthly.nc"
    return f"{base_url}/{filename}"
```

### 2. URL Validation

**Function:** `_validate_url(url: str) -> bool`

**Purpose:** Verify that a URL points to an existing file before attempting download

**Implementation:**
```python
def _validate_url(url: str, timeout: int = 10) -> bool:
    """
    Validate that a URL exists and is accessible.
    
    Parameters
    ----------
    url : str
        URL to validate
    timeout : int
        Request timeout in seconds
        
    Returns
    -------
    bool
        True if URL returns HTTP 200, False otherwise
    """
    try:
        response = requests.head(url, timeout=timeout)
        if response.status_code == 200:
            log_info(f"URL validated successfully: {url}")
            return True
        else:
            log_error(f"URL validation failed with status {response.status_code}: {url}")
            return False
    except requests.exceptions.RequestException as e:
        log_error(f"URL validation error: {e}")
        return False
```

### 3. Data Authenticity Verification

**Function:** `_verify_data_authenticity(df: pd.DataFrame) -> dict`

**Purpose:** Verify that fetched data is real and not synthetic

**Implementation:**
```python
def _verify_data_authenticity(df: pd.DataFrame) -> dict:
    """
    Verify that the data appears to be real CHIRPS data.
    
    Checks:
    - Rainfall values are within realistic ranges for Tanzania
    - Data does not match synthetic generation patterns
    - Sufficient temporal coverage
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with rainfall data
        
    Returns
    -------
    dict
        Verification results with keys:
        - is_authentic: bool
        - statistics: dict with min, max, mean, std
        - warnings: list of warning messages
    """
    warnings = []
    
    # Check rainfall ranges (Tanzania: 0-500mm/month typical)
    min_rain = df['rainfall_mm'].min()
    max_rain = df['rainfall_mm'].max()
    mean_rain = df['rainfall_mm'].mean()
    std_rain = df['rainfall_mm'].std()
    
    if min_rain < 0:
        warnings.append("Negative rainfall values detected")
    if max_rain > 1000:
        warnings.append("Unrealistically high rainfall values detected")
    if mean_rain < 10 or mean_rain > 300:
        warnings.append("Mean rainfall outside typical Tanzania range")
    
    # Check for synthetic data patterns (gamma distribution artifacts)
    # Real data should have more variability and irregular patterns
    if std_rain < 10:
        warnings.append("Low variability suggests synthetic data")
    
    # Check temporal coverage
    if len(df) < 12:
        warnings.append("Insufficient temporal coverage")
    
    is_authentic = len(warnings) == 0
    
    statistics = {
        'min': min_rain,
        'max': max_rain,
        'mean': mean_rain,
        'std': std_rain,
        'count': len(df)
    }
    
    return {
        'is_authentic': is_authentic,
        'statistics': statistics,
        'warnings': warnings
    }
```

### 4. Enhanced Error Handling

**Approach:** Categorize errors and provide specific guidance

**Error Categories:**
1. **Network Errors** - Connection timeout, DNS failure
2. **HTTP Errors** - 404 (file not found), 403 (forbidden), 500 (server error)
3. **Processing Errors** - Invalid NetCDF format, missing dimensions
4. **Validation Errors** - Data outside expected ranges

**Implementation Pattern:**
```python
try:
    # Download attempt
    response = requests.get(url, timeout=120)
    response.raise_for_status()
except requests.exceptions.Timeout:
    log_error(f"Network timeout while downloading {url}")
    log_error("Suggestion: Check internet connection or increase timeout")
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        log_error(f"File not found (404): {url}")
        log_error("Suggestion: Verify year is within CHIRPS coverage (1981-present)")
    elif e.response.status_code == 403:
        log_error(f"Access forbidden (403): {url}")
        log_error("Suggestion: Check if authentication is required")
    else:
        log_error(f"HTTP error {e.response.status_code}: {url}")
except Exception as e:
    log_error(f"Unexpected error downloading {url}: {e}")
```

## Data Models

### Input Parameters
```python
{
    'dry_run': bool,           # Skip actual download
    'start_year': int,         # First year to fetch (default: 2010)
    'end_year': int,           # Last year to fetch (default: 2023)
    'bounds': dict             # Geographic bounding box
}
```

### Output DataFrame Schema
```python
{
    'year': int,               # Year of observation
    'month': int,              # Month (1-12)
    'rainfall_mm': float,      # Mean monthly rainfall (mm)
    'lat_min': float,          # Bounding box minimum latitude
    'lat_max': float,          # Bounding box maximum latitude
    'lon_min': float,          # Bounding box minimum longitude
    'lon_max': float,          # Bounding box maximum longitude
    'data_source': str         # 'chirps_api' or 'cached' or 'synthetic'
}
```

### Verification Results Schema
```python
{
    'is_authentic': bool,      # Overall authenticity flag
    'statistics': {
        'min': float,          # Minimum rainfall
        'max': float,          # Maximum rainfall
        'mean': float,         # Mean rainfall
        'std': float,          # Standard deviation
        'count': int           # Number of records
    },
    'warnings': list[str]      # List of warning messages
}
```

## Error Handling

### Error Scenarios and Responses

| Scenario | Detection | Response | User Impact |
|----------|-----------|----------|-------------|
| Invalid URL (404) | HTTP status code | Log error with URL, try next year | Partial data if some years succeed |
| Network timeout | requests.Timeout | Log error, suggest connection check | Retry or use cached data |
| Invalid NetCDF | xarray exception | Log error, skip year | Partial data if some years succeed |
| All downloads fail | Empty data list | Raise exception, do NOT generate synthetic data | Pipeline fails with clear error |
| Synthetic data detected | Authenticity check | Log warning, mark data source | User warned about data quality |

### Fallback Strategy

**Current (Problematic):**
```
API fails → Use cached data → Generate synthetic data
```

**Proposed (Strict):**
```
API fails → Use cached data → Raise exception with diagnostic info
```

**Rationale:** Synthetic data should never be used silently. If real data cannot be fetched, the user must be informed explicitly so they can take corrective action.

### Logging Strategy

**Log Levels:**
- **INFO**: Successful downloads, validation passes, data statistics
- **WARNING**: Using cached data, authenticity concerns, partial failures
- **ERROR**: Download failures, invalid data, processing errors

**Key Log Messages:**
```python
# Success
log_info(f"Successfully downloaded CHIRPS data for {year} from {url}")
log_info(f"Data authenticity verified: {statistics}")

# Warnings
log_warning("Using cached CHIRPS data instead of fresh API data")
log_warning(f"Data authenticity concerns: {warnings}")

# Errors
log_error(f"Failed to download CHIRPS data for {year}: HTTP {status_code}")
log_error(f"URL validation failed: {url}")
log_error("No CHIRPS data was successfully fetched from API")
```

## Testing Strategy

### Unit Tests

**Test File:** `tests/test_chirps_ingestion.py`

**Test Cases:**

1. **test_construct_url_correct_format**
   - Verify URL includes `byYear/` subdirectory
   - Verify filename uses `.monthly.nc` suffix
   - Test multiple years

2. **test_validate_url_success**
   - Mock HEAD request returning 200
   - Verify function returns True
   - Verify correct logging

3. **test_validate_url_failure**
   - Mock HEAD request returning 404
   - Verify function returns False
   - Verify error logging

4. **test_verify_authenticity_real_data**
   - Create DataFrame with realistic Tanzania rainfall
   - Verify authenticity check passes
   - Verify statistics are calculated correctly

5. **test_verify_authenticity_synthetic_data**
   - Create DataFrame with synthetic patterns
   - Verify authenticity check fails
   - Verify warnings are generated

6. **test_fetch_with_correct_url**
   - Mock successful download with real URL pattern
   - Verify data is fetched and processed
   - Verify no fallback to synthetic data

7. **test_fetch_all_years_fail**
   - Mock all downloads failing
   - Verify exception is raised
   - Verify no synthetic data is generated

### Integration Tests

**Test File:** `tests/integration/test_chirps_api.py`

**Test Cases:**

1. **test_real_api_download**
   - Fetch data for single recent year (e.g., 2023)
   - Verify HTTP 200 response
   - Verify NetCDF file is valid
   - Verify data is processed correctly

2. **test_multiple_years_download**
   - Fetch data for 2-3 years
   - Verify all years are fetched successfully
   - Verify data continuity

3. **test_invalid_year**
   - Attempt to fetch data for year before 1981
   - Verify appropriate error handling

### Manual Testing Checklist

- [ ] Delete existing `chirps_raw.csv` file
- [ ] Run ingestion with `dry_run=False`
- [ ] Verify log messages show correct URLs
- [ ] Verify HTTP 200 responses in logs
- [ ] Verify data statistics are logged
- [ ] Verify output file contains real data
- [ ] Compare output with previous synthetic data to confirm differences
- [ ] Test with different year ranges
- [ ] Test with network disconnected (should fail gracefully)

## Implementation Notes

### Dependencies

No new dependencies required. Existing dependencies are sufficient:
- `requests` - HTTP requests
- `xarray` - NetCDF processing
- `pandas` - Data manipulation
- `numpy` - Numerical operations

### Performance Considerations

**File Sizes:**
- Each yearly NetCDF file: ~170MB
- Download time: 30-60 seconds per year (depends on connection)
- Processing time: 5-10 seconds per year

**Optimization:**
- Downloads are sequential (one year at a time)
- Could be parallelized in future if needed
- Temporary files are cleaned up immediately after processing

### Backward Compatibility

**Breaking Changes:**
- Synthetic data generation is removed from automatic fallback
- Function will raise exception instead of silently generating fake data

**Migration Path:**
- Users relying on synthetic data must explicitly use `dry_run=True`
- Cached data will still be used if available
- Clear error messages guide users to corrective actions

### Configuration

**No configuration changes required.** The fix is entirely in the URL construction logic.

**Optional Future Enhancement:**
Add configuration option to specify CHIRPS data source:
```python
# In config.py or .env
CHIRPS_BASE_URL = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/netcdf/byYear"
CHIRPS_FILENAME_PATTERN = "chirps-v2.0.{year}.monthly.nc"
```

## Design Decisions and Rationales

### Decision 1: Remove Automatic Synthetic Data Generation

**Rationale:** Silently using synthetic data when real data is available creates a false sense of security. Users should be explicitly aware when they're not using real data. This prevents incorrect insurance calculations based on fake data.

**Alternative Considered:** Keep synthetic fallback but add prominent warnings
**Why Rejected:** Warnings can be missed in logs. Hard failure forces users to address the root cause.

### Decision 2: Use HEAD Request for URL Validation

**Rationale:** HEAD requests are lightweight (no body download) and quickly verify file existence before committing to a large download. This saves bandwidth and time when URLs are incorrect.

**Alternative Considered:** Try download and catch errors
**Why Rejected:** Wastes bandwidth downloading potentially large files that will fail.

### Decision 3: Keep Year-by-Year Download Approach

**Rationale:** Maintains current architecture, easier to debug, and allows partial success if some years fail.

**Alternative Considered:** Download single consolidated file
**Why Rejected:** CHIRPS provides year-by-year files, and this approach allows incremental updates.

### Decision 4: Add Data Source Column to Output

**Rationale:** Enables downstream processes to know whether data came from API, cache, or (in dry_run mode) synthetic generation.

**Alternative Considered:** Separate metadata file
**Why Rejected:** Keeping metadata with data is simpler and reduces file management complexity.

## Security Considerations

- **No authentication required:** CHIRPS data is publicly accessible
- **HTTPS used:** All downloads use secure HTTPS protocol
- **No sensitive data:** Rainfall data is public domain
- **Input validation:** Year ranges are validated to prevent injection attacks
- **Timeout limits:** Prevent indefinite hanging on network issues

## Future Enhancements

1. **Parallel Downloads:** Use `concurrent.futures` to download multiple years simultaneously
2. **Resume Capability:** Track downloaded years and skip already-fetched data
3. **Alternative Data Sources:** Support CHIRPS data from Google Earth Engine or other mirrors
4. **Daily Data Support:** Add option to fetch daily instead of monthly data
5. **Automatic Updates:** Periodically check for new data and update cache
6. **Data Quality Metrics:** More sophisticated authenticity checks using climatological baselines
