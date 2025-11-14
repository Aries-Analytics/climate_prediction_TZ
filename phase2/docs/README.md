# Tanzania Climate Prediction - Phase 2 Documentation

## Overview

This directory contains comprehensive internal documentation for the Phase 2 data pipeline. The documentation is designed for developers working on the pipeline and includes detailed technical information, code examples, and operational guides.

## Documentation Files

### 📋 [pipeline_overview.md](pipeline_overview.md)
**Complete pipeline architecture and design**

- Pipeline architecture with visual diagrams
- Data flow through ingestion, processing, and merge stages
- Module descriptions and interfaces
- Directory structure
- Execution modes (debug vs production)
- Performance metrics
- Known limitations and future enhancements

### 📊 [data_dictionary.md](data_dictionary.md)
**Comprehensive data schemas and formats**

- Raw data schemas for all 5 sources (NASA POWER, ERA5, CHIRPS, NDVI, Ocean Indices)
- Processed data schemas
- Master dataset structure
- Column definitions with types, units, and ranges
- Data quality notes
- Units and conversions
- Example data samples
- Validation rules

### 🚀 [pipeline_run_instructions.md](pipeline_run_instructions.md)
**Step-by-step operational guide**

- Prerequisites and system requirements
- Environment setup (.env and CDS API configuration)
- Running the pipeline (debug and production modes)
- Running individual modules
- Test execution
- CI/CD workflows
- Comprehensive troubleshooting guide
- Performance optimization tips
- Scheduling automated runs

### 🔧 [feature_engineering.md](feature_engineering.md)
**Feature engineering guide for ML models**

- **✅ NEW:** Implemented features in processing modules (148+ features)
- Temporal features (seasons, lags, rolling statistics)
- Climate interaction features
- Vegetation features from NDVI
- Anomaly detection features
- Derived meteorological features
- Feature selection methods
- Complete pipeline example
- Best practices and integration guide

### ⚙️ [PROCESSING_MODULES_COMPLETE.md](PROCESSING_MODULES_COMPLETE.md)
**✅ NEW: Complete processing modules documentation**

- Detailed feature descriptions for all 5 processing modules
- CHIRPS: Drought/flood indicators with SPI and insurance triggers
- NDVI: Vegetation health (VCI), crop failure risk
- Ocean Indices: ENSO/IOD indicators, climate forecasts, early warnings
- NASA POWER: Temperature and solar radiation features
- ERA5: Atmospheric indicators
- Design principles and implementation details
- 148+ total engineered features

### 📑 [PROCESSING_FEATURES_SUMMARY.md](PROCESSING_FEATURES_SUMMARY.md)
**✅ NEW: Quick reference guide to all features**

- Complete feature list with descriptions and ranges
- Features organized by module and category
- Usage examples and code snippets
- Feature interpretation guide (risk scores, SPI, VCI)
- Insurance payout logic examples
- Quick lookup tables for all 186+ features

### 📈 [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)
**✅ UPDATED: Current implementation status**

- **100% complete** - All core features implemented
- Feature completion metrics and statistics
- Code quality metrics
- Next steps and future enhancements
- Known issues and limitations

## Quick Start

### For New Developers

1. **Read first:** [pipeline_overview.md](pipeline_overview.md) - Understand the architecture
2. **Setup environment:** Follow [pipeline_run_instructions.md](pipeline_run_instructions.md)
3. **Run in debug mode:** Test the pipeline without real API calls
4. **Explore data:** Review [data_dictionary.md](data_dictionary.md) for schemas

### For Running the Pipeline

```bash
# Quick test (uses mock data, < 1 minute)
python run_pipeline.py --debug

# Production run (real data, 10-30 minutes)
python run_pipeline.py
```

### For Understanding Data

```bash
# Check the data dictionary
cat docs/data_dictionary.md

# View output
head outputs/processed/master_dataset.csv
```

## Code Documentation

All code modules include comprehensive docstrings following NumPy/SciPy documentation style. These docstrings are ready for auto-generation with Sphinx or MkDocs.

### Docstring Format

```python
def function_name(param1, param2):
    """
    Brief description of what the function does.
    
    Longer description with more details about the function's behavior,
    algorithms used, and important notes.

    Parameters
    ----------
    param1 : type
        Description of param1.
    param2 : type, optional
        Description of param2. Default is value.

    Returns
    -------
    return_type
        Description of what is returned.

    Raises
    ------
    ExceptionType
        When this exception is raised.

    Notes
    -----
    Additional information, implementation details, or important warnings.

    Examples
    --------
    >>> from module import function_name
    >>> result = function_name(arg1, arg2)
    >>> print(result)
    """
```

### Modules with Docstrings

**Ingestion Modules:**
- `modules/ingestion/nasa_power_ingestion.py`
- `modules/ingestion/era5_ingestion.py`
- `modules/ingestion/chirps_ingestion.py`
- `modules/ingestion/ndvi_ingestion.py`
- `modules/ingestion/ocean_indices_ingestion.py`

**Processing Modules:**
- `modules/processing/process_nasa_power.py`
- `modules/processing/process_era5.py`
- `modules/processing/process_chirps.py`
- `modules/processing/process_ndvi.py`
- `modules/processing/process_ocean_indices.py`
- `modules/processing/merge_processed.py`

**Utility Modules:**
- `utils/config.py`
- `utils/logger.py`
- `utils/validator.py`
- `utils/validation.py`

## Generating API Documentation

### Using Sphinx

```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme

# Initialize Sphinx (in docs/ directory)
cd docs
sphinx-quickstart

# Configure conf.py to include your modules
# Add to conf.py:
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # For NumPy-style docstrings
    'sphinx.ext.viewcode',
]

# Generate documentation
sphinx-apidoc -o source/ ../modules ../utils
make html

# View documentation
open _build/html/index.html
```

### Using MkDocs

```bash
# Install MkDocs
pip install mkdocs mkdocs-material mkdocstrings[python]

# Create mkdocs.yml
cat > mkdocs.yml << EOF
site_name: Tanzania Climate Prediction Pipeline
theme:
  name: material

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            docstring_style: numpy

nav:
  - Home: index.md
  - Pipeline Overview: pipeline_overview.md
  - Data Dictionary: data_dictionary.md
  - Run Instructions: pipeline_run_instructions.md
  - Feature Engineering: feature_engineering.md
  - API Reference:
    - Ingestion: api/ingestion.md
    - Processing: api/processing.md
    - Utilities: api/utilities.md
EOF

# Serve documentation locally
mkdocs serve

# Build static site
mkdocs build
```

## Documentation Standards

### When to Update Documentation

- **Adding new modules:** Update pipeline_overview.md and add docstrings
- **Changing data schemas:** Update data_dictionary.md
- **Modifying pipeline flow:** Update pipeline_overview.md
- **Adding features:** Update feature_engineering.md
- **Fixing bugs:** Update troubleshooting section in pipeline_run_instructions.md

### Documentation Checklist

When adding new functionality:

- [ ] Add comprehensive docstrings to all functions
- [ ] Include parameter types and descriptions
- [ ] Provide usage examples
- [ ] Document exceptions and error conditions
- [ ] Update relevant markdown documentation
- [ ] Add to data dictionary if new data schemas
- [ ] Update pipeline overview if architecture changes

## Getting Help

### Documentation Issues

If you find errors or gaps in the documentation:

1. Check if the issue is already documented in troubleshooting
2. Review the relevant code docstrings
3. Check logs for detailed error messages
4. Open an issue on GitHub with details

### Code Issues

For code-related problems:

1. Review [pipeline_run_instructions.md](pipeline_run_instructions.md) troubleshooting section
2. Check logs in `logs/pipeline_YYYY-MM-DD.log`
3. Run in debug mode to isolate issues
4. Review module docstrings for usage examples

## Contributing

When contributing to the pipeline:

1. **Follow docstring format:** Use NumPy/SciPy style
2. **Update documentation:** Keep markdown docs in sync with code
3. **Add examples:** Include usage examples in docstrings
4. **Test thoroughly:** Run tests and verify documentation accuracy
5. **Review checklist:** Complete documentation checklist above

## Additional Resources

### External Documentation

- [NASA POWER API](https://power.larc.nasa.gov/docs/)
- [Copernicus CDS API](https://cds.climate.copernicus.eu/api-how-to)
- [CHIRPS Dataset](https://www.chc.ucsb.edu/data/chirps)
- [NOAA Climate Indices](https://www.cpc.ncep.noaa.gov/)

### Python Documentation Tools

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [MkDocs Documentation](https://www.mkdocs.org/)
- [NumPy Docstring Guide](https://numpydoc.readthedocs.io/en/latest/format.html)

## Version History

- **v1.0** (2024-11-14): Initial documentation release
  - Complete pipeline overview
  - Data dictionary for all sources
  - Run instructions and troubleshooting
  - Feature engineering guide
  - Comprehensive docstrings in all modules

---

**Last Updated:** 2024-11-14  
**Maintained By:** Tanzania Climate Prediction Team
