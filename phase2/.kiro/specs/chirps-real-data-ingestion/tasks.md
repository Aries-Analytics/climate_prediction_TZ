# Implementation Plan

- [ ] 1. Update URL construction to use correct CHIRPS API endpoint





  - Modify the `fetch_chirps_data` function to use the correct base URL with `byYear/` subdirectory
  - Change filename pattern from `.months_p05.nc` to `.monthly.nc`
  - Update the `CHIRPS_BASE_URL` constant to point to the correct directory
  - _Requirements: 1.1, 2.1, 2.2_

- [ ] 2. Add URL validation before download
- [ ] 2.1 Create `_construct_chirps_url` helper function
  - Write function that takes a year parameter and returns the complete CHIRPS URL
  - Use the correct URL pattern: `{base_url}/byYear/chirps-v2.0.{year}.monthly.nc`
  - Add docstring with parameters and return value documentation
  - _Requirements: 2.1, 2.2_

- [ ] 2.2 Create `_validate_url` helper function
  - Write function that performs HEAD request to verify URL exists
  - Return boolean indicating if URL is accessible (HTTP 200)
  - Add timeout parameter with default of 10 seconds
  - Log validation results (success or failure with status code)
  - Handle network exceptions gracefully
  - _Requirements: 2.4, 3.1_

- [ ] 2.3 Integrate URL validation into download flow
  - Call `_validate_url` before attempting to download each year's data
  - Skip download if validation fails and log the failed URL
  - Continue with next year if one year fails validation
  - _Requirements: 2.4, 3.2_

- [ ] 3. Implement data authenticity verification
- [ ] 3.1 Create `_verify_data_authenticity` helper function
  - Write function that takes a DataFrame and returns verification results dictionary
  - Check rainfall values are within realistic ranges (0-1000mm/month for Tanzania)
  - Calculate statistics: min, max, mean, standard deviation, count
  - Detect synthetic data patterns (low variability, unrealistic distributions)
  - Return dictionary with `is_authentic`, `statistics`, and `warnings` keys
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 3.2 Integrate authenticity verification into fetch flow
  - Call `_verify_data_authenticity` after processing all downloaded data
  - Log verification results including statistics
  - Log warnings if authenticity concerns are detected
  - Add `data_source` column to output DataFrame indicating 'chirps_api', 'cached', or 'synthetic'
  - _Requirements: 4.4, 4.5_

- [ ] 4. Enhance error handling and logging
- [ ] 4.1 Improve error categorization in download logic
  - Add specific exception handling for `requests.exceptions.Timeout`
  - Add specific exception handling for `requests.exceptions.HTTPError` with status code checks
  - Add specific exception handling for `xarray` processing errors
  - Provide actionable error messages for each error type
  - _Requirements: 3.1, 3.4_

- [ ] 4.2 Update logging throughout the module
  - Log the exact URL being attempted for each year
  - Log HTTP status codes for failed requests
  - Log file sizes for successful downloads
  - Log data statistics after processing (min, max, mean rainfall)
  - Add warning log when using cached data instead of fresh API data
  - _Requirements: 2.5, 3.1, 3.3, 3.5_

- [ ] 4.3 Remove automatic synthetic data fallback
  - Remove or comment out the call to `_generate_sample_chirps_data` in the main error handling
  - Raise a clear exception when no data is successfully fetched from API
  - Keep the `_generate_sample_chirps_data` function for `dry_run=True` mode only
  - Update exception message to guide users on corrective actions
  - _Requirements: 1.5, 3.3_

- [ ] 5. Update function to handle partial success scenarios
  - Modify the logic to continue processing remaining years if some years fail
  - Ensure that if at least one year succeeds, return the available data
  - Only raise exception if ALL years fail to download
  - Log summary of successful vs failed years at the end
  - _Requirements: 3.2, 3.3_

- [ ] 6. Add data source tracking
  - Add `data_source` column to the output DataFrame
  - Set value to 'chirps_api' for freshly downloaded data
  - Set value to 'cached' when using existing cached file
  - Set value to 'synthetic' when in dry_run mode
  - Include data source in validation output
  - _Requirements: 4.5_

- [ ]* 7. Create unit tests for new helper functions
  - Write test for `_construct_chirps_url` with multiple years
  - Write test for `_validate_url` with mocked successful response (200)
  - Write test for `_validate_url` with mocked failed response (404)
  - Write test for `_verify_data_authenticity` with realistic data
  - Write test for `_verify_data_authenticity` with synthetic-looking data
  - Write test for `_verify_data_authenticity` with out-of-range values
  - _Requirements: 4.1, 4.2, 4.3_

- [ ]* 8. Create integration test for real API access
  - Write test that fetches data for a single recent year (2023)
  - Verify HTTP 200 response is received
  - Verify NetCDF file is successfully processed
  - Verify output DataFrame has expected structure
  - Verify data statistics are within realistic ranges
  - Mark as integration test (may require network access)
  - _Requirements: 1.1, 1.2, 1.3_

- [ ]* 9. Update module docstring and function documentation
  - Update module-level docstring to reflect correct API endpoint
  - Update `fetch_chirps_data` docstring with correct URL examples
  - Add notes about data authenticity verification
  - Document the new `data_source` column in output schema
  - Add examples showing how to verify data is real vs synthetic
  - _Requirements: 5.2_
