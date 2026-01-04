# Exploratory Data Analysis (EDA) Results

## Overview

This directory contains comprehensive EDA results for the Tanzania Climate Prediction pipeline datasets.

## Generated Files

### Before Merging (`before_merge/`)
Individual EDA for each processed dataset:
- **CHIRPS** (Rainfall): 48 records, 42 features
- **NDVI** (Vegetation): 36 records, 47 features  
- **Ocean Indices** (Climate): 48 records, 61 features
- **NASA POWER** (Temperature/Solar): 24 records, 18 features
- **ERA5** (Atmospheric): 2 records, 3 features

Each dataset includes:
- `*_eda_report.txt` - Comprehensive text report
- `*_distributions.png` - Feature distribution plots
- `*_correlations.png` - Correlation heatmap
- `*_timeseries.png` - Time series plots (if temporal data)
- `*_missing_values.png` - Missing value patterns (if applicable)

### After Merging (`after_merge/`)
EDA for the merged master dataset:
- **MERGED**: 48 records, 160 features
- Combines all data sources with intelligent merging
- 69.62% row reduction (from 158 to 48 rows)
- 5 new columns added during merge

Includes same visualization types as individual datasets.

### Comparison (`merge_comparison_report.txt`)
Detailed comparison of datasets before and after merging:
- Row and column counts
- Data reduction statistics
- New features created
- Merge strategy summary

## Key Findings

### Merged Dataset Statistics
- **Total Features**: 160 (152 numeric, 8 categorical)
- **Time Range**: 2020-01-01 to 2023-12-01 (3.92 years)
- **Missing Values**: 986 total across 63 columns
- **High Correlations**: 796 feature pairs with |r| > 0.7
- **Memory Usage**: 0.08 MB

### Missing Value Patterns
Top features with missing values:
1. `ndvi_change_yoy`: 100% (expected - requires 12-month lag)
2. NASA POWER features: 50% (24 months of data vs 48 total)
3. Various derived features with lag dependencies

### High Correlations
Notable perfect correlations (r = 1.0):
- `iod` ↔ `iod_impact_score` (by design)
- `crop_failure_risk` ↔ `trigger_severity` (by design)
- `temp_mean_c` ↔ `heat_index_c` (expected)
- `rainfall_anomaly` ↔ `rainfall_deficit` (inverse relationship)

### Data Quality
- **No gaps** in time series (continuous monthly data)
- **Consistent temporal coverage** across most sources
- **ERA5 data limited** (only 2 records - needs attention)
- **NASA POWER partial coverage** (24 of 48 months)

## How to Use These Results

### 1. Review Reports
Start with the text reports for quick overview:
```bash
# Merged dataset summary
cat outputs/eda/after_merge/MERGED_eda_report.txt

# Individual dataset summaries
cat outputs/eda/before_merge/CHIRPS_eda_report.txt
cat outputs/eda/before_merge/NDVI_eda_report.txt
# etc.
```

### 2. Examine Visualizations
Open PNG files to see:
- Distribution patterns (identify skewness, outliers)
- Correlation structures (identify multicollinearity)
- Time series trends (identify seasonality, trends)
- Missing value patterns (identify systematic gaps)

### 3. Identify Issues
Use EDA to find:
- **Missing data**: Features with >50% missing
- **Outliers**: Extreme values in distributions
- **Multicollinearity**: High correlations (|r| > 0.9)
- **Data gaps**: Temporal discontinuities
- **Imbalanced features**: Skewed distributions

### 4. Inform Feature Engineering
Based on EDA insights:
- Remove highly correlated features (reduce redundancy)
- Impute or drop features with excessive missing values
- Transform skewed features (log, sqrt, box-cox)
- Create interaction terms for uncorrelated but related features
- Engineer lag features where temporal patterns exist

### 5. Guide Model Development
Use EDA to:
- Select relevant features for modeling
- Determine preprocessing needs (scaling, encoding)
- Identify target variable characteristics
- Estimate model complexity requirements
- Plan cross-validation strategy

## Regenerating EDA

To regenerate EDA after pipeline updates:

```bash
# Run full pipeline first
python run_pipeline.py --debug

# Then run EDA
python run_eda.py
```

EDA will automatically:
- Detect processed datasets
- Analyze each dataset individually
- Analyze merged dataset
- Generate comparison report
- Create all visualizations

## Next Steps

Based on EDA results:

1. **Address ERA5 Data**: Only 2 records - investigate ingestion issue
2. **Handle Missing Values**: Decide on imputation strategy for NASA POWER
3. **Feature Selection**: Remove redundant highly correlated features
4. **Feature Engineering**: Create targeted interaction features
5. **Model Training**: Use insights to guide model selection and tuning

## Technical Details

### EDA Module
- **Location**: `utils/eda.py`
- **Runner Script**: `run_eda.py`
- **Dependencies**: pandas, numpy, matplotlib, seaborn

### Analysis Components
1. Basic statistics (shape, dtypes, memory)
2. Missing value analysis (counts, percentages)
3. Distribution analysis (mean, median, skewness, kurtosis)
4. Correlation analysis (Pearson correlation matrix)
5. Time series patterns (gaps, trends, seasonality)
6. Feature statistics (unique values, zeros, ranges)
7. Visualizations (distributions, correlations, time series)
8. Comprehensive reports (text summaries)

---

**Generated**: 2024-11-14  
**Pipeline Version**: Phase 2  
**Data Sources**: CHIRPS, NDVI, Ocean Indices, NASA POWER, ERA5
