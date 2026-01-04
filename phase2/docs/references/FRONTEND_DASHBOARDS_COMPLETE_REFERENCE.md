# Frontend Dashboards - Complete Feature Reference
**Last Updated**: January 3, 2026  
**Status**: ✅ Production Ready

This document serves as the comprehensive reference for all frontend dashboard capabilities, consolidating enhancements across Executive Snapshot, Model Performance, Trigger Events, and Climate Insights dashboards.

---

## 🎯 1. Executive Command Center

**Purpose**: Strategic overview of crop insurance portfolio health, operational efficiency, and financial sustainability.

### 1.1 Core KPI Cards (Top Row)

All KPI cards now feature **visible color-coded info blocks** instead of hidden tooltips for better visual clarity.

#### Farmers Covered
- **Value**: 12,500-17,500 (simulated)
- **Status**: Green (Success)
- **Trend**: Upward (+12% vs LY)
- **Info Block**: *"Unique policyholders with active coverage"* (Blue)

#### Hectares Insured
- **Value**: 45,000-55,000 ha (simulated)
- **Status**: Green (Success)
- **Est. Yield Value**: Calculated at $450/ha
- **Info Block**: *"Total land area covered. Estimated yield based on crop type"* (Blue)

#### Replanting Speed
- **Value**: 12-27 Days (simulated)
- **Status**: Dynamic
  - Green (< 14 days): Excellent
  - Orange (14-21 days): Good
  - Red (> 21 days): Missed Replanting Window
- **Critical Threshold**: 21-day window for crop replanting
- **Info Block**: *"Avg days from Trigger to Payout. Target < 14 Days"* (Color-coded by status)

#### Loss Ratio (YTD)
- **Value**: 40%-120% (simulated, includes crisis scenarios)
- **Status**: Dynamic
  - Green (< 60%): Sustainable
  - Orange (60-80%): Monitor Closely
  - Red (> 80%): UNSUSTAINABLE
- **Info Block**: *"Payouts / Premiums collected. >80% is Critical"* (Color-coded by status)

### 1.2 Strategic Charts

#### Financial Solvency Trend (5-Year)
- **Type**: Line chart with threshold indicators
- **Y-Axis**: Loss Ratio (0-120%)
- **Threshold Lines**:
  - Orange dash (60%): Warning threshold
  - Red dash (80%): Critical threshold
- **Simulation Logic**:
  - Starting Capital: $20M
  - Annual Premiums: $10M (constant)
  - Random Loss Ratios: 40%-120%
  - Cumulative accounting: `Reserves = Prev_Reserves + Premiums - Payouts`
- **Color Coding**: Line turns red when LR > 80%
- **Insight Block**: Dynamic message explaining fund health
  - Green: "Fund is healthy. Retained earnings are growing"
  - Orange: "CAUTION: Loss ratio approaching break-even point"
  - Red: "UNSUSTAINABLE: Claims exceed 80% of premiums. Immediate capital injection required"

#### Capital Utilization & Liquidity (NEW)
- **Type**: Grouped bar chart
- **Metrics**:
  - Orange bars: Annual Payouts ($2M-$12M)
  - Green bars: Cumulative Reserves (can shrink in crisis scenarios)
- **Mathematical Relationship**: Directly driven by Loss Ratio
  - Formula: `Payout = Premiums × Loss_Ratio`
  - Formula: `Reserves_Year_N = Reserves_Year_(N-1) + Premiums - Payout`
- **Crisis Scenarios**: When Loss Ratio > 100%, green bars shrink year-over-year
- **Info Block**: *"Reserves (Green) vs Payouts (Orange). Gap indicates safety margin"* (Blue)

#### Basis Risk Indicator (Model Accuracy)
- **Type**: Scatter plot
- **Axes**:
  - X-Axis: VHI (Vegetation Health Index, 0=Dead Crops, 1=Healthy)
  - Y-Axis: Severity (%)
- **Marker Types**:
  - Green circles: Paid (Success) - model triggered payout correctly
  - Red X: No Payout - potential false negatives
- **Critical Zone**: LEFT side (VHI < 0.3, No Payout) = Basis Risk
- **Use Case**: Identifies crop failures where parametric model failed to trigger
- **Info Block**: *"X-Axis = VHI (0=Dead Crops, 1=Healthy). Red X markers on the LEFT side (VHI < 0.3, No Payout) are False Negatives (Basis Risk)"* (Blue)

### 1.3 Global Alert System
- **Warning Alert** (Orange): Shows when N regions have potential basis risk
- **Success Alert** (Green): Shows when portfolio is healthy

### 1.4 Data Simulation Transparency
- **Badge**: "SIMULATION DATA" chip in header
- **Simulated**: Metric values (randomized each year selection)
- **Real**: 6 Pilot Region names (Arusha, Dar es Salaam, Dodoma, Mbeya, Mwanza, Morogoro)
- **Scale Demo**: 4 additional regions for watchlist demonstration

---

## 📊 2. Model Performance Dashboard

**Purpose**: Machine learning model evaluation, transparency, and scientific validity.

### 2.1 Temporal Leakage Prevention
- **Visual Timeline**: Shows strict temporal ordering
  - Training: 2000-2018 (1,090 samples)
  - Validation: 2018-2021 (230 samples)
  - Test: 2022-2025 (240 samples)
- **Guarantee**: No future data leaks into training
- **Scientific Validity**: Ensures realistic performance estimates

### 2.2 Performance Metrics

#### Primary Metrics
- **R² (Coefficient of Determination)**
  - Range: 0-1
  - Threshold: ≥ 0.85 (Green = Excellent)
  - Current: ~0.87-0.92 across locations
- **RMSE (Root Mean Square Error)**
  - Lower is better
  - Context: Scaled to climate variable units
- **MAE (Mean Absolute Error)**
  - Interpretable error in original units

#### Statistical Confidence
- **95% Confidence Intervals**: Displayed for all CV metrics
- **Standard Deviations**: Shows model stability across folds
- **Cross-Validation**: 5-fold temporal CV

#### Baseline Comparisons
- **Ridge Regression**: Simple linear baseline
- **Persistence Model**: "Tomorrow = Today" baseline
- **Mean Baseline**: Historical average
- **Purpose**: Proves complex models (XGBoost, Random Forest) add value

### 2.3 Data Quality Indicators
- **Feature-to-Sample Ratio**: 12.82:1 (Target > 10:1)
- **Sample Breakdown**: Detailed counts across splits
- **Missing Data Handling**: Documented imputation strategies

### 2.4 Visualizations

#### Observed vs Predicted
- **Type**: Time series overlay
- **Purpose**: Visual validation of model predictions
- **Bands**: Confidence intervals around predictions

#### Feature Importance
- **Type**: Horizontal bar chart
- **Color**: Gradient (light to dark blue)
- **Tooltips**: Exact importance values
- **Top Drivers**: Identifies key climate predictors

---

## 🗺️ 3. Trigger Events Dashboard

**Purpose**: Real-time monitoring of parametric insurance triggers and geographic risk distribution.

### 3.1 Geographic Map Component

#### Choropleth Layer (Regional Heatmap)
- **Data Source**: Tanzania administrative regions GeoJSON
- **Color Scale** (Payout-based):
  - Gray: $0 (No risk)
  - Light Blue: $1-9,999 (Low risk)
  - Yellow: $10k-49k (Medium risk)
  - Orange: $50k-99k (High risk)
  - Red: $100k+ (Extreme risk)
- **Geometry Support**: Both Polygon and MultiPolygon regions
- **Data Parsing**: Handles API string coordinates (Decimal types)

#### Interactive Features
- **Time-Lapse Animation**:
  - Play/Pause controls
  - Month slider (Jan-Dec)
  - Speed toggle: 1x (800ms) / 2x (400ms)
  - Auto-loop on completion
- **Impact Layer Toggles**:
  - Payout (Financial impact)
  - Severity (Crop damage %)
  - Frequency (Trigger count)
  - Context-sensitive tooltips with icons ($, ⚠️, 📊)
- **Zoom Controls**: Disabled scroll zoom to prevent map hijacking
- **Map Legend**: Dynamic value ranges based on selected metric

#### Marker System
- **City-Level Indicators**: 6 calibrated locations
- **Color Coding by Trigger Type**:
  - Blue: Drought
  - Green: Flood
  - Orange: Crop Failure
- **Rich Tooltips**: Location, status, severity, payout amount
- **Event Breakdown**: Shows counts by trigger type for each region

### 3.2 KPI Cards (Top Row)
- **Total Financial Exposure**: Cumulative payout liability
- **Trigger Frequency**: Event count (baseline ~23.5/year, warning > 40/year)
- **Avg. Severity**: Percentage measure (>60% = valid trigger)
- **Business Logic Context**: Educational info blocks explaining thresholds

### 3.3 Chart Visualizations

#### Trigger Type Breakdown
- **Type**: Donut chart
- **Metrics**: Payout distribution by peril (Drought, Flood, Crop Failure)
- **Purpose**: Portfolio composition analysis

#### Severity Distribution
- **Type**: Histogram
- **Bins**: 10% intervals (0-100%)
- **Insight**: "Fat tail" on right (>80%) indicates high-impact events

#### Regional Risk Comparison
- **Type**: Horizontal bar chart
- **Sorted**: By total payout (descending)
- **Dynamic**: Uses fetched location names from API
- **Tooltip**: Shows trigger event count per region

#### Financial Sustainability Tracker
- **Type**: Dual-line chart
- **Lines**:
  - Blue: Cumulative Payouts
  - Red: Budget Limit (Premium pool)
- **Alert**: When blue crosses red, Loss Ratio > 100%
- **Purpose**: Visual loss ratio tracking

### 3.4 Layout Optimization
- **Grid Structure**: 50/50 split for Severity Distribution and Trigger Type charts
- **Full-Width Financial Tracker**: 12-column span for visibility
- **Export Button**: Top header placement for clean UX

---

## 🌡️ 4. Climate Insights Dashboard

**Purpose**: Exploratory data analysis, trend identification, and historical climate pattern recognition.

### 4.1 Interactive Time Series Analysis

#### Filter Persistence (NEW)
- **Behavior**: Time range selections persist when toggling variables
- **UX Improvement**: Users don't lose zoomed-in view when adding/removing data series
- **State Management**: Decoupled time filter from variable selection

#### Decoupled Variable Filtering (NEW)
- **Top Selector**: Only affects main time series chart
- **Statistical Charts**: Always show all variables regardless of selection
- **Rationale**: Allows decluttering main view while retaining full statistical context

#### Dynamic Controls
- **Zoom & Pan**: Interactive chart navigation
- **Range Selectors**: Quick buttons (1Y, 5Y, 10Y, All)
- **Fixed Range Logic**: Prevents users from getting lost in empty space
- **Legend Position**: Below chart to prevent data blocking
- **Optimal Height**: 450px for visibility

### 4.2 Statistical Distributions

#### Box Plots (Temperature & Rainfall)
- **Displays**: Spread, median (Q2), quartiles, outliers
- **Purpose**: Identify extreme months that trigger payouts
- **Visibility**: Always visible even if variable deselected from main chart
- **Use Case**: Basis risk detection (outlier analysis)

### 4.3 Seasonal Analysis

#### Monthly Averages Chart
- **Aggregation**: By month (Jan-Dec)
- **Purpose**: Reveal seasonal patterns
  - Long Rains "Masika" (Mar-May)
  - Short Rains "Vuli" (Oct-Dec)
- **Critical for**: Identifying shifts in seasonality due to climate change

### 4.4 Advanced Analytics

#### Rolling Window Metrics
- **Window**: 12-month sliding average
- **Purpose**: Smooth noise, reveal long-term trends
- **Detection**: Warming trends, drying patterns
- **Visual**: Overlaid on main time series

#### Extreme Events Histograms
- **Tail Risk Analysis**: Shows frequency of extreme values
- **Mapping**: Directly relates to parametric trigger thresholds (e.g., 95th percentile)
- **Use Case**: Calibrating insurance payout tiers

#### Temperature vs Rainfall Scatter
- **Purpose**: Identify compound risk scenarios
- **Quadrants**:
  - Hot & Dry: Drought risk
  - Cool & Wet: Flood risk
  - Hot & Wet: Heat stress + disease
  - Cool & Dry: Crop stress
- **Color Coding**: By density or time period

---

## 🔧 Technical Implementation

### Frontend Stack
- **Framework**: React 18 + TypeScript
- **UI Library**: Material-UI (MUI) v5
- **Charts**: Plotly.js (interactive) + react-plotly.js
- **Maps**: React-Leaflet + Leaflet
- **State Management**: React hooks (useState, useMemo, useEffect)
- **Styling**: MUI theme system + sx props

### Performance Optimizations
- **Memoization**: `useMemo` for expensive calculations
- **Chart Config**: `scrollZoom: false` to prevent page hijacking
- **Lazy Loading**: Dynamic imports for heavy components
- **Debouncing**: Filter inputs to reduce re-renders

### Data Handling
- **Coordinate Parsing**: `parseFloat()` for API Decimal types (strings)
- **GeoJSON Preservation**: Maintains FeatureCollection structure for maps
- **Null Safety**: Graceful handling of missing data
- **Type Safety**: TypeScript interfaces for all props

### Deployment
- **Container**: Docker (development mode)
- **Hot Reload**: Requires `docker-compose restart frontend` for certain changes
- **Build**: Vite (fast HMR)
- **Port**: 3000 (default)

---

## 📋 Consolidated Feature Changelog

### January 3, 2026
- ✅ Executive Dashboard: Added Capital Utilization chart
- ✅ Executive Dashboard: Extended Loss Ratio simulation to 120% (bankruptcy scenarios)
- ✅ Executive Dashboard: Converted all tooltips to visible info blocks
- ✅ Executive Dashboard: Fixed Basis Risk description (LEFT side clarification)
- ✅ All Dashboards: Improved y-axis spacing (standoff property)
- ✅ Capital chart: Implemented mathematically consistent reserves calculation

### January 1-2, 2026
- ✅ Geographic Map: Time-lapse animation with 2x speed toggle
- ✅ Geographic Map: Impact layer toggles (Payout/Severity/Frequency)
- ✅ Geographic Map: Context-sensitive tooltips with icons
- ✅ Geographic Map: Dynamic legend with value ranges
- ✅ Trigger Dashboard: Replaced raw tables with Financial Sustainability Tracker
- ✅ Trigger Dashboard: Optimized chart layout (50/50 splits)
- ✅ Climate Insights: Filter persistence implementation
- ✅ Climate Insights: Decoupled variable filtering
- ✅ Model Performance: Temporal leakage prevention visualization
- ✅ Model Performance: Feature importance gradient styling

---

## 🗂️ Related Documentation

**Consolidates**:
- `FRONTEND_MAP_INTEGRATION_SUMMARY.md` (Map features)
- `GEOGRAPHIC_MAP_DEBUGGING.md` (Technical debugging guide)
- Previous `DASHBOARD_COMPREHENSIVE_SUMMARY.md` (Climate Insights, Model Performance)

**See Also**:
- `GETTING_STARTED.md`: User credentials and setup
- `PROJECT_OVERVIEW.md`: High-level architecture
- `PARAMETRIC_INSURANCE_DASHBOARD_METRICS.md`: Business logic reference

---

**Maintained by**: Frontend Development Team  
**Next Review**: When API integration replaces mock data
