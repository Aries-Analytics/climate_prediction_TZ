# Requirements Document: Historical Data Migration (2010-2025)

## Introduction

This specification defines requirements for migrating the complete 2010-2025 historical climate dataset into the PostgreSQL database. The system currently contains only 2018-2023 data (93 recent records), but the full merged dataset with 15+ years of data exists in `data/processed/merged_data_2010_2025.csv`. This migration will enable the dashboard to display comprehensive historical trends and improve model validation.

## Glossary

- **Historical Dataset**: The complete merged climate data from 2010-2025 (188 months) located at `data/processed/merged_data_2010_2025.csv`
- **Database**: PostgreSQL database running in Docker container for the climate dashboard
- **Climate Data Table**: The `climate_data` table storing monthly climate observations
- **Data Migration**: The process of loading historical data from CSV into the database
- **Upsert Operation**: Insert new records or update existing records if they already exist
- **Data Verification**: Post-migration checks to ensure data integrity and completeness

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want to load the complete 2010-2025 historical dataset into the database, so that the dashboard displays 15+ years of climate data instead of just 6 years.

#### Acceptance Criteria

1. WHEN the migration script executes THEN the system SHALL read `data/processed/merged_data_2010_2025.csv`
2. WHEN the CSV is parsed THEN the system SHALL validate that all required columns are present
3. WHEN records are processed THEN the system SHALL transform CSV data to match database schema
4. WHEN data is inserted THEN the system SHALL use upsert logic to update existing records and insert new ones
5. WHEN migration completes THEN the system SHALL report total records processed and inserted

### Requirement 2

**User Story:** As a system administrator, I want the migration to handle existing data gracefully, so that I don't lose the recent forecast data already in the database.

#### Acceptance Criteria

1. WHEN duplicate records are detected THEN the system SHALL update existing records with historical data
2. WHEN new records are encountered THEN the system SHALL insert them into the database
3. WHEN migration runs THEN the system SHALL preserve any forecast records not in the historical CSV
4. WHEN conflicts occur THEN the system SHALL log which records were updated vs inserted
5. WHEN migration completes THEN the system SHALL maintain referential integrity across all tables

### Requirement 3

**User Story:** As a system administrator, I want to verify data integrity after migration, so that I can confirm the dashboard will display accurate information.

#### Acceptance Criteria

1. WHEN verification runs THEN the system SHALL confirm record count matches expected 188 months (2010-2025)
2. WHEN date ranges are checked THEN the system SHALL verify data spans from January 2010 to November 2025
3. WHEN data quality is validated THEN the system SHALL check for null values in critical fields
4. WHEN statistics are calculated THEN the system SHALL verify reasonable ranges for temperature, rainfall, and NDVI
5. WHEN verification completes THEN the system SHALL generate a summary report with pass/fail status

### Requirement 4

**User Story:** As a data analyst, I want the migration to map all CSV columns to database fields, so that no important climate data is lost during the transfer.

#### Acceptance Criteria

1. WHEN temperature data is mapped THEN the system SHALL store temp_mean_c, temp_max_c, and temp_min_c
2. WHEN rainfall data is mapped THEN the system SHALL store rainfall_mm and related precipitation metrics
3. WHEN vegetation data is mapped THEN the system SHALL store ndvi, vci, and vegetation health indicators
4. WHEN climate indices are mapped THEN the system SHALL store oni, iod, enso_phase, and related fields
5. WHEN trigger flags are mapped THEN the system SHALL store drought_trigger, flood_trigger, and crop_failure_trigger

### Requirement 5

**User Story:** As a system administrator, I want the migration to be transactional, so that partial failures don't corrupt the database.

#### Acceptance Criteria

1. WHEN migration starts THEN the system SHALL begin a database transaction
2. WHEN errors occur during processing THEN the system SHALL rollback all changes
3. WHEN migration succeeds THEN the system SHALL commit the transaction
4. WHEN rollback occurs THEN the system SHALL restore the database to pre-migration state
5. WHEN errors are logged THEN the system SHALL include specific error messages and affected records

### Requirement 6

**User Story:** As a system administrator, I want to see progress during migration, so that I know the operation is running and not stuck.

#### Acceptance Criteria

1. WHEN migration starts THEN the system SHALL display total records to process
2. WHEN records are processed THEN the system SHALL show progress every 10 records
3. WHEN batches complete THEN the system SHALL display percentage complete
4. WHEN migration finishes THEN the system SHALL show total time elapsed
5. WHEN errors occur THEN the system SHALL display error count and continue processing

### Requirement 7

**User Story:** As a data analyst, I want the dashboard to automatically reflect the new historical data, so that I can immediately view 15-year trends.

#### Acceptance Criteria

1. WHEN migration completes THEN the system SHALL make data available to API endpoints immediately
2. WHEN dashboard queries execute THEN the system SHALL return data from 2010-2025 range
3. WHEN time series charts render THEN the system SHALL display 188 months of data
4. WHEN date filters are applied THEN the system SHALL allow selection from 2010-2025 range
5. WHEN KPIs are calculated THEN the system SHALL use the full historical dataset

### Requirement 8

**User Story:** As a system administrator, I want to handle data type conversions correctly, so that numeric and boolean fields are stored properly.

#### Acceptance Criteria

1. WHEN numeric fields are processed THEN the system SHALL convert string values to float or integer
2. WHEN boolean fields are processed THEN the system SHALL convert 0/1 or True/False to boolean
3. WHEN null values are encountered THEN the system SHALL store them as NULL in the database
4. WHEN date fields are processed THEN the system SHALL validate year and month are within valid ranges
5. WHEN conversion fails THEN the system SHALL log the error and skip the problematic field

### Requirement 9

**User Story:** As a system administrator, I want to backup the database before migration, so that I can restore if something goes wrong.

#### Acceptance Criteria

1. WHEN backup is requested THEN the system SHALL create a PostgreSQL dump file
2. WHEN backup completes THEN the system SHALL verify the dump file is valid
3. WHEN backup location is set THEN the system SHALL store dump in specified directory
4. WHEN backup fails THEN the system SHALL abort migration and report error
5. WHEN restore is needed THEN the system SHALL provide instructions for restoring from backup

### Requirement 10

**User Story:** As a developer, I want clear documentation on running the migration, so that I can execute it correctly and troubleshoot issues.

#### Acceptance Criteria

1. WHEN documentation is accessed THEN the system SHALL provide step-by-step migration instructions
2. WHEN prerequisites are listed THEN the system SHALL specify required files and database state
3. WHEN command examples are shown THEN the system SHALL include actual commands to run
4. WHEN troubleshooting guide is provided THEN the system SHALL list common errors and solutions
5. WHEN verification steps are documented THEN the system SHALL explain how to confirm successful migration

### Requirement 11

**User Story:** As a system administrator, I want to run the migration from both inside and outside Docker, so that I have flexibility in execution environment.

#### Acceptance Criteria

1. WHEN running from host THEN the system SHALL connect to database via localhost:5432
2. WHEN running from Docker THEN the system SHALL connect to database via service name
3. WHEN environment variables are set THEN the system SHALL use them for database connection
4. WHEN connection fails THEN the system SHALL provide clear error message about connectivity
5. WHEN migration completes THEN the system SHALL work regardless of execution environment

### Requirement 12

**User Story:** As a data analyst, I want the migration to preserve data provenance, so that I can trace where each record came from.

#### Acceptance Criteria

1. WHEN records are inserted THEN the system SHALL preserve the _provenance_files column
2. WHEN data source is tracked THEN the system SHALL maintain information about source CSV files
3. WHEN metadata is stored THEN the system SHALL include migration timestamp
4. WHEN audit trail is needed THEN the system SHALL log which records came from historical migration
5. WHEN data lineage is queried THEN the system SHALL show original source files for each record

### Requirement 13

**User Story:** As a system administrator, I want to handle large datasets efficiently, so that migration completes in reasonable time.

#### Acceptance Criteria

1. WHEN bulk insert is used THEN the system SHALL process records in batches of 100
2. WHEN database writes occur THEN the system SHALL use prepared statements for performance
3. WHEN indexes exist THEN the system SHALL temporarily disable them during bulk insert
4. WHEN migration completes THEN the system SHALL rebuild indexes
5. WHEN performance is measured THEN the system SHALL complete migration in under 5 minutes

### Requirement 14

**User Story:** As a system administrator, I want to validate the CSV file before migration, so that I catch issues early.

#### Acceptance Criteria

1. WHEN validation runs THEN the system SHALL check that CSV file exists and is readable
2. WHEN headers are validated THEN the system SHALL verify all required columns are present
3. WHEN data types are checked THEN the system SHALL verify numeric columns contain valid numbers
4. WHEN date ranges are validated THEN the system SHALL confirm years are between 2010-2025
5. WHEN validation fails THEN the system SHALL abort migration and report specific issues

### Requirement 15

**User Story:** As a data analyst, I want to compare before and after statistics, so that I can verify the migration improved data coverage.

#### Acceptance Criteria

1. WHEN pre-migration stats are collected THEN the system SHALL record current record count and date range
2. WHEN post-migration stats are collected THEN the system SHALL record new record count and date range
3. WHEN comparison is displayed THEN the system SHALL show records added and date range expansion
4. WHEN statistics are calculated THEN the system SHALL show min/max/avg for key climate variables
5. WHEN report is generated THEN the system SHALL highlight the improvement in data coverage
