# Requirements Document

## Introduction

The CHIRPS (Climate Hazards Group InfraRed Precipitation with Station data) ingestion module currently fails to fetch real data from the UCSB Climate Hazards Center API and falls back to generating synthetic sample data. This feature will fix the ingestion module to properly fetch real CHIRPS rainfall data from the API, ensuring that the climate risk insurance pipeline uses authentic precipitation data for Tanzania.

## Glossary

- **CHIRPS**: Climate Hazards Group InfraRed Precipitation with Station data - a high-resolution rainfall dataset
- **UCSB CHC**: University of California Santa Barbara Climate Hazards Center - the provider of CHIRPS data
- **Ingestion Module**: The `modules/ingestion/chirps_ingestion.py` file responsible for fetching CHIRPS data
- **NetCDF**: Network Common Data Form - a file format for storing multidimensional scientific data
- **API Endpoint**: The URL from which CHIRPS data files are downloaded
- **Fallback Data**: Synthetic sample data generated when real API data cannot be fetched
- **Tanzania Bounds**: Geographic bounding box covering Tanzania (lat: -11.75 to -0.99, lon: 29.34 to 40.44)

## Requirements

### Requirement 1

**User Story:** As a data engineer, I want the CHIRPS ingestion module to successfully fetch real rainfall data from the UCSB Climate Hazards Center API, so that the insurance pipeline uses authentic precipitation data instead of synthetic fallback data.

#### Acceptance Criteria

1. WHEN THE Ingestion Module attempts to download CHIRPS data, THE Ingestion Module SHALL use the correct API endpoint URL structure that returns HTTP 200 status codes
2. WHEN THE Ingestion Module receives a successful response from the API, THE Ingestion Module SHALL download NetCDF files containing real CHIRPS precipitation data
3. WHEN THE Ingestion Module completes a data fetch, THE Ingestion Module SHALL verify that the downloaded data is authentic by checking for valid NetCDF structure and realistic rainfall values
4. WHEN THE Ingestion Module encounters a 404 error, THE Ingestion Module SHALL log the specific URL that failed and attempt alternative URL patterns
5. THE Ingestion Module SHALL NOT generate synthetic fallback data when the API endpoint is accessible and returns valid data

### Requirement 2

**User Story:** As a data engineer, I want the ingestion module to discover and use the correct CHIRPS file naming conventions and directory structure, so that data downloads succeed for all requested years.

#### Acceptance Criteria

1. WHEN THE Ingestion Module constructs a download URL, THE Ingestion Module SHALL use the correct file naming convention that matches the UCSB CHC server structure
2. WHEN THE Ingestion Module requests data for a specific year, THE Ingestion Module SHALL construct URLs that point to existing files on the server
3. IF THE Ingestion Module encounters a 404 error for a specific file pattern, THEN THE Ingestion Module SHALL attempt alternative file naming patterns documented by UCSB CHC
4. THE Ingestion Module SHALL validate that the constructed URL returns HTTP 200 status before attempting full file download
5. WHEN THE Ingestion Module successfully downloads a file, THE Ingestion Module SHALL log the exact URL pattern used for future reference

### Requirement 3

**User Story:** As a data engineer, I want the ingestion module to handle API errors gracefully and provide clear diagnostic information, so that I can troubleshoot issues when data fetching fails.

#### Acceptance Criteria

1. WHEN THE Ingestion Module encounters an HTTP error, THE Ingestion Module SHALL log the HTTP status code, URL, and error message
2. WHEN THE Ingestion Module fails to download data for a specific year, THE Ingestion Module SHALL continue attempting to download data for remaining years
3. IF THE Ingestion Module fails to download any data after trying all years, THEN THE Ingestion Module SHALL raise a clear exception indicating that no real data was fetched
4. THE Ingestion Module SHALL distinguish between network errors, HTTP errors, and data processing errors in log messages
5. WHEN THE Ingestion Module uses cached data, THE Ingestion Module SHALL log a warning that cached data is being used instead of fresh API data

### Requirement 4

**User Story:** As a data engineer, I want the ingestion module to validate that fetched data is real and not synthetic, so that I can trust the data quality for insurance calculations.

#### Acceptance Criteria

1. WHEN THE Ingestion Module completes a data fetch, THE Ingestion Module SHALL check that rainfall values fall within realistic ranges for the Tanzania region
2. THE Ingestion Module SHALL verify that the data does not match the synthetic data generation pattern (gamma distribution with seed 42)
3. WHEN THE Ingestion Module processes NetCDF data, THE Ingestion Module SHALL verify that the data contains valid latitude, longitude, and time dimensions
4. THE Ingestion Module SHALL calculate and log basic statistics (min, max, mean rainfall) to enable manual verification of data authenticity
5. IF THE Ingestion Module detects that the data appears to be synthetic, THEN THE Ingestion Module SHALL log a warning and mark the data source in the output file

### Requirement 5

**User Story:** As a data engineer, I want to investigate the current CHIRPS API structure and documentation, so that I can determine the correct endpoints and file formats to use.

#### Acceptance Criteria

1. THE Ingestion Module SHALL support both monthly and daily CHIRPS data file formats based on availability
2. WHEN THE Ingestion Module discovers the API structure, THE Ingestion Module SHALL document the correct base URL, directory paths, and file naming conventions
3. THE Ingestion Module SHALL check for the existence of alternative CHIRPS data sources if the primary endpoint is unavailable
4. THE Ingestion Module SHALL support CHIRPS version 2.0 data format as currently implemented
5. IF THE Ingestion Module finds that CHIRPS data requires authentication or API keys, THEN THE Ingestion Module SHALL document the authentication requirements and provide clear error messages
