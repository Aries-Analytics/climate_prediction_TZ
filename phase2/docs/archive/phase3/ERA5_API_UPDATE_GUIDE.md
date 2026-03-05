# ERA5 API Configuration Guide

## Current Setup (March 2026)

ERA5 data is fetched via the **`ecmwf-datastores-client`** library (v0.4.2), the official ECMWF Data Stores API client.

> **Note:** The old `cdsapi` library is deprecated and had DNS/connection failures. Migrated March 4, 2026.

## Configuration

### Environment Variables (preferred)

```
ECMWF_DATASTORES_URL=https://cds.climate.copernicus.eu/api
ECMWF_DATASTORES_KEY=your-api-key-here
```

These are set in `docker-compose.dev.yml` for the pipeline-scheduler service.

### Config File (fallback)

Create `~/.ecmwfdatastoresrc`:

```
url: https://cds.climate.copernicus.eu/api
key: your-api-key-here
```

### Getting Credentials

1. Register at: https://cds.climate.copernicus.eu
2. API key page: https://cds.climate.copernicus.eu/how-to-api
3. Key format: UUID only (no `UID:` prefix)

## Installation

```bash
pip install ecmwf-datastores-client
```

## Code Location

- **Ingestion module:** `modules/ingestion/era5_ingestion.py`
- **Import:** `from ecmwf.datastores import Client`
- **Collection:** `reanalysis-era5-single-levels-monthly-means`

## Reference

- Documentation: https://ecmwf.github.io/ecmwf-datastores-client/
- Migration guide: https://confluence.ecmwf.int/display/CKB/Please+read%3A+CDS+and+ADS+migrated+to+new+infrastructure
