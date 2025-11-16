# Reporting Scripts

Scripts for generating business metrics reports and visualizations.

## Scripts

### `generate_business_reports.py`

Main script to generate all business-focused reports from climate data.

**Usage:**
```bash
# From project root
python scripts/reporting/generate_business_reports.py

# With custom data source
python scripts/reporting/generate_business_reports.py --data path/to/data.csv

# With custom output directory
python scripts/reporting/generate_business_reports.py --output path/to/output/
```

**Generates:**
- Executive summary (Markdown)
- Insurance trigger details (CSV)
- Alert timeline (CSV)
- Financial impact analysis (CSV)
- Risk dashboard (JSON)
- Visualizations (PNG charts)

**Requirements:**
- Master dataset must exist at `outputs/processed/master_dataset.csv`
- Dataset must contain trigger columns (drought_trigger, flood_trigger, etc.)

**Output Location:**
- Default: `outputs/business_reports/`
- Visualizations: `outputs/business_reports/visualizations/`

## Related Modules

The reporting scripts use these core modules:
- `reporting/business_metrics.py` - Report generation engine
- `reporting/visualize_business_metrics.py` - Visualization generator

## Documentation

See `docs/BUSINESS_REPORTS_GUIDE.md` for complete documentation on:
- Report interpretation
- Customization options
- Integration examples
- Troubleshooting
