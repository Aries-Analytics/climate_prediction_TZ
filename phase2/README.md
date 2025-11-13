# Tanzania Climate Prediction - Phase 2

A comprehensive data pipeline for ingesting, processing, and analyzing climate data from multiple sources to support climate prediction modeling for Tanzania.

## Overview

Phase 2 focuses on building a robust data pipeline that:
- Ingests climate data from 5 major sources (NASA POWER, ERA5, CHIRPS, NDVI, Ocean Indices)
- Processes and validates data with comprehensive error handling
- Merges datasets into a unified master dataset
- Provides a testing framework to ensure data quality

## Project Structure

```
phase2/
├── modules/
│   ├── ingestion/          # Data ingestion modules
│   │   ├── nasa_power_ingestion.py
│   │   ├── era5_ingestion.py
│   │   ├── chirps_ingestion.py
│   │   ├── ndvi_ingestion.py
│   │   └── ocean_indices_ingestion.py
│   └── processing/         # Data processing modules
│       ├── process_nasa_power.py
│       ├── process_era5.py
│       ├── process_chirps.py
│       ├── process_ndvi.py
│       ├── process_ocean_indices.py
│       └── merge_processed.py
├── utils/
│   ├── config.py          # Configuration and path management
│   ├── logger.py          # Logging utilities
│   ├── validator.py       # Data validation functions
│   └── validation.py      # Additional validation helpers
├── tests/
│   ├── test_pipeline.py   # Pipeline integration tests
│   └── test_merge_processed.py  # Merge functionality tests
├── data/
│   ├── raw/              # Raw ingested data
│   ├── processed/        # Processed data
│   └── external/         # External data sources
├── outputs/
│   └── processed/        # Final processed outputs
├── run_pipeline.py       # Main pipeline execution script
├── requirements.txt      # Python dependencies
└── pytest.ini           # Pytest configuration
```

## Data Sources

### 1. NASA POWER
- **Source**: NASA Prediction of Worldwide Energy Resources
- **Data**: Temperature, solar radiation
- **API**: https://power.larc.nasa.gov/api/temporal/monthly/point

### 2. ERA5
- **Source**: ECMWF Reanalysis v5
- **Data**: Temperature, humidity, atmospheric variables
- **Access**: Requires API key

### 3. CHIRPS
- **Source**: Climate Hazards Group InfraRed Precipitation with Station data
- **Data**: Rainfall measurements
- **URL**: https://data.chc.ucsb.edu/products/CHIRPS-2.0

### 4. NDVI
- **Source**: Normalized Difference Vegetation Index
- **Data**: Vegetation health indicators
- **Format**: Satellite imagery data

### 5. Ocean Indices
- **Source**: NOAA Climate Indices
- **Data**: ENSO, IOD (Indian Ocean Dipole)
- **URL**: https://psl.noaa.gov/data/climateindices/list/

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/lordwalt/climate_prediction_TZ.git
cd climate_prediction_TZ/phase2
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.template .env
# Edit .env with your API keys and configuration
```

## Usage

### Running the Pipeline

**Dry-run mode (with mock data):**
```bash
python run_pipeline.py --debug
```

**Production mode (with real data):**
```bash
python run_pipeline.py
```

### Running Tests

**Run all tests:**
```bash
pytest -v
```

**Run specific test suite:**
```bash
pytest tests/test_pipeline.py -v
pytest tests/test_merge_processed.py -v
```

**Run with coverage:**
```bash
pytest --cov=modules --cov=utils -v
```

## Configuration

### Environment Variables

Create a `.env` file based on `.env.template`:

```env
# NASA POWER API
NASA_API_URL=https://power.larc.nasa.gov/api/temporal/monthly/point

# ERA5 API
ERA5_API_KEY=your_api_key_here

# CHIRPS Data
CHIRPS_BASE_URL=https://data.chc.ucsb.edu/products/CHIRPS-2.0

# NDVI Source
NDVI_SOURCE=your_ndvi_source

# Ocean Indices
OCEAN_INDICES_SOURCE=https://psl.noaa.gov/data/climateindices/list/

# Project Settings
DEFAULT_REGION=Tanzania
DEFAULT_CRS=EPSG:4326
```

## Pipeline Workflow

1. **Ingestion**: Fetch raw data from all sources
2. **Validation**: Validate data structure and content
3. **Processing**: Transform and clean data
4. **Merging**: Combine all processed datasets
5. **Output**: Save master dataset in CSV and Parquet formats

## Data Validation

The pipeline includes comprehensive validation:
- **Structure checks**: Ensures data is in DataFrame format
- **Column validation**: Verifies expected columns exist
- **Empty data detection**: Catches empty datasets
- **Missing value warnings**: Logs columns with null values

## Output Files

Processed data is saved in `outputs/processed/`:
- `nasa_power_processed.csv`
- `era5_processed.csv`
- `chirps_processed.csv`
- `ndvi_processed.csv`
- `ocean_indices_processed.csv`
- `master_dataset.csv` - Combined dataset
- `master_dataset.parquet` - Optimized format

## Testing

The project includes comprehensive tests:

### Test Coverage
- Pipeline integration tests (dry-run mode)
- Data merge functionality tests
- Validation utility tests

### Test Markers
```bash
# Run only pipeline tests
pytest -m pipeline

# Run with verbose output
pytest -v

# Run with debug logging
pytest -s
```

## Logging

Logs are stored in `logs/` directory:
- Pipeline execution logs
- Validation results
- Error traces
- Data processing summaries

## Development

### Adding New Data Sources

1. Create ingestion module in `modules/ingestion/`
2. Create processing module in `modules/processing/`
3. Add to pipeline in `run_pipeline.py`
4. Update tests

### Code Style
- Follow PEP 8 guidelines
- Use type hints where applicable
- Document functions with docstrings
- Keep functions focused and modular

## Troubleshooting

### Common Issues

**Import errors:**
```bash
# Ensure you're in the phase2 directory
cd phase2
python run_pipeline.py
```

**Missing dependencies:**
```bash
pip install -r requirements.txt
```

**API authentication errors:**
- Check your `.env` file has correct API keys
- Verify API endpoints are accessible

**Empty DataFrame errors:**
- Run in debug mode first: `python run_pipeline.py --debug`
- Check data source availability
- Review logs in `logs/` directory

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `pytest -v`
4. Commit with descriptive messages
5. Push and create a pull request

## License

This project is part of the Tanzania Climate Prediction initiative.

## Contact

For questions or issues, please open an issue on GitHub.

## Acknowledgments

- NASA POWER for climate data
- ECMWF for ERA5 reanalysis data
- Climate Hazards Group for CHIRPS rainfall data
- NOAA for ocean indices data
