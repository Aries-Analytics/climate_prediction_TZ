# Frontend Dashboards - Complete Reference

**Last Updated**: April 2, 2026
**Version**: 2.2 (Landing Page Added)

## 📌 Overview
This document serves as the single source of truth for all frontend dashboards and pages in the HewaSense Early Warning System.

> **Note**: For detailed architecture and backend logic of the Climate Pivot, see [Climate Index Pivot Reference](../climate_pivot/climate_index_pivot_reference.md).

## 0. Public Landing Page (Live)
**Route**: `/` (was `<Navigate to="/dashboard/executive" />` — changed March 16, 2026)
**URL**: `hewasense.majaribio.com`
**Stack**: Tailwind CSS v3 + shadcn/ui coexisting with MUI v5

**Purpose**: Public-facing entry point for HewaSense. Communicates the platform's value proposition, pilot status, and provides access to the authenticated dashboard.

### Components (`src/components/landing/`)
| Component | Purpose |
|---|---|
| `LandingNavbar.tsx` | Fixed, scroll-aware, responsive navigation |
| `HeroSection.tsx` | Full-viewport dark navy hero with CTAs |
| `StatsBar.tsx` | 4 KPIs (1,000 farmers, 25 yrs historical, 3 perils, 86.7% accuracy) + Shadow Run Active amber badge |
| `HowItWorksSection.tsx` | 4-step pipeline explanation (outcomes only, no architecture exposure) |
| `FeaturesSection.tsx` | 6 feature cards (one per dashboard module) |
| `AboutSection.tsx` | Mission + spec table |
| `AccessCTASection.tsx` | Shadow run framing — real forecasts, no real payouts yet |
| `LandingFooter.tsx` | Brand, nav links, copyright 2026 |

### Copy Policy
Public copy describes **outcomes only**. XGBoost is acceptable to name. Never expose: model architecture details, R² thresholds, horizon counts, internal service names.

### Stats (canonical)
- Farmers: **1,000** (exact — not 1,000+)
- Historical data: **25 years**
- Perils monitored: **3** (drought, flood, crop failure — not "12 forecast horizons")
- Accuracy: **86.7% R²** (6-location dataset, XGBoost post data-leakage fix)

---

## 1. Climate Index Insurance Dashboard (New!)
**Route**: `/forecast` (Replaces legacy Forecast Dashboard)

The primary operational dashboard for monitoring climate risks (Rainfall) against parametric insurance thresholds.

### Key Components
1.  **Active Payout Triggers**:
    *   Real-time list of locations where projected rainfall fails to meet thresholds.
    *   Shows **Phenology Stage** (e.g., Flowering) and **Deviation** metrics.
2.  **Climate Forecast Chart**:
    *   **Visualization**: Line chart with Confidence Intervals (Shaded Area).
    *   **Thresholds**: Dynamic red/green zones indicating Required Rainfall for the specific crop stage.
    *   **Interactive Tooltips**: Shows stage-specific advice.

### Data Sources
- **Forecasts**: `/api/climate-forecasts/` (Rainfall predictions)
- **Alerts**: `/api/climate-forecasts/alerts` (Trigger logic)

---

## 2. Executive Command Center
**Route**: `/executive`

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

### 2.5 Forecast Validation & Model Performance (NEW - Jan 2026)

#### Validation Metrics Section
- **Purpose**: Track model accuracy in predicting actual trigger events
- **Data Source**: `GET /api/forecasts/validation`
- **Metrics Displayed**:
  - **Accuracy**: % of correct predictions (trigger occurred when predicted)
  - **Precision**: Of high-probability forecasts, how many actually triggered
  - **Recall**: Of actual events, how many were predicted
  - **Brier Score**: Probabilistic accuracy (0 = perfect, 1 = worst)
- **Breakdown**: By trigger type (drought, flood, crop_failure) and horizon (3-6 months)
- **Color Coding**:
  - 🟢 Green (≥75%): Excellent performance
  - 🟡 Yellow (60-75%): Good performance
  - 🔴 Red (<60%): Needs retraining

#### Drift Detection & Retraining Alerts
- **Automatic Monitoring**: Compares accuracy against 60% threshold
- **Alert Banner**: Displays when models need retraining
- **Specific Recommendations**: Lists exact trigger type + horizon combinations
- **Status Indicators**: Visual green checkmark or red warning per model

---

## 🚨 5. Early Warning System Dashboard

**Purpose**: 3-6 month probabilistic forecasts for climate-related insurance triggers.

### 5.1 Forecast Freshness Indicator (NEW - Jan 2026)

**Color-Coded Status Banner**:
- 🟢 **Green** (Success): Forecasts < 3 days old
- 🟡 **Yellow** (Warning): Forecasts 3-7 days old
- 🔴 **Red** (Error): Forecasts > 7 days old (stale, need updating)

**Information Displayed**:
- Last update timestamp (localized)
- Total forecasts in database
- Next scheduled auto-update time
- Staleness warning when forecasts exceed 7 days

**Data Source**: `GET /api/forecasts/scheduler/status`

### 5.2 Validation Metrics Summary (NEW - Jan 2026)

**Quick Accuracy Overview**: Displayed before forecast timeline chart

**Features**:
- Shows up to 6 most recent validation metrics
- Compact cards with trigger type chips
- Accuracy percentage (color-coded)
- Precision and Recall summary
- Link to full details in Model Performance dashboard

**Purpose**: Build user confidence in forecast reliability

### 5.3 Core Forecast Features

#### Forecast Timeline Chart
- **Horizon**: 3, 4, 5, and 6-month ahead predictions
- **Trigger Types**: Drought, flood, crop_failure
- **Probability Display**: 0-1 scale with confidence intervals
- **Risk Threshold**: Red dashed line at 75% probability (Severe Risk)
- **Color Coding**: Orange (drought), Blue (flood), Red (crop failure)
- **Line Styles**: Solid (3mo), Dash (4mo), Dot (5mo), Dash-Dot (6mo)

#### High-Risk Forecasts Summary
- **Filter**: Probability > 75%
- **Display**: Cards showing trigger type, horizon, target date
- **Confidence Intervals**: Lower and upper bounds displayed

#### Recommendations Panel
- **Trigger**: Auto-generated when probability > 75%
- **Priority Levels**: High, Medium, Low (color-coded)
- **Content**: Actionable advice specific to trigger type
- **Timeline**: Action deadlines included

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
- **Hot Reload**: Requires `docker compose restart frontend` for certain changes
- **Build**: Vite (fast HMR)
- **Port**: 3000 (default)

---

## 📋 Consolidated Feature Changelog

### January 5, 2026
- ✅ Model Performance Dashboard: Added forecast validation metrics section
- ✅ Model Performance Dashboard: Implemented drift detection and retraining alerts
- ✅ Early Warning Dashboard: Added forecast freshness indicator
- ✅ Early Warning Dashboard: Added validation metrics summary cards
- ✅ Both Dashboards: Integrated validation API endpoints

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

---

## April 2026 — Live Dashboard Changes (Real Data, Shadow Run Active)

> These changes apply to the production live dashboards served from `hewasense.majaribio.com`. All data is real (no simulation).

### ExecutiveDashboard.tsx — Forecast Risk Landscape grid
- **TRIGGER chip** replaced with **OFF-SEASON badge** (grey) for primary-tier (3–4 month) forecasts where `stage === 'off_season'`. Wet-season pilot covers Jan–Jun only; Aug–Sep forecasts can be high-probability (dry season) but have no insured crop attached.
- Red TRIGGER badge now only shows for in-season primary-tier forecasts ≥75%.
- Legend updated: added OFF-SEASON entry explaining "≥75% but no insured crop — no payout."

### RiskManagementDashboard.tsx — KPI cards
- **"Loss Ratio"** KPI card split into two distinct cards:
  - **"Reserve Stress Ratio"** — forward 6-month probability-weighted projection, capped at 200%. Answers: "how stressed are reserves if this season triggers?" Signal, not sustainability verdict.
  - **"Actuarial Loss Ratio"** — 22.6% historical 10-yr backtested. Answers: "is the $20 premium sustainably priced?" This is the product health metric.
- **"Sustainability Status"** card renamed **"Pricing Sustainability"** — now evaluates `historicalLossRatio` (22.6%), not the forward stress ratio. 22.6% → "Sustainably Priced" (green).
- Scenario analysis legend text updated to explain the scenario loss ratio is a reserve stress test, not an actuarial metric.

### TriggersDashboard.tsx — Language corrections
- Page subtitle: "active insurance triggers" → "forecast-based probability alerts". Clarifies payouts trigger on *observed* breach, not forecast probability alone.
- Threshold summary bar: "active payout alert" → "high-probability forecast alert (primary tier ≥75% — not confirmed observed breach)."
- `PayoutActionCard` receives `shadowRunActive={true}` — button locked, card renamed to "Parametric Reserve Requirement."

### PayoutActionCard.tsx — Shadow run awareness
- Added `shadowRunActive?: boolean` prop (default `true`).
- When `true`: card title = "Parametric Reserve Requirement", amount label = "Probability-Weighted Reserve Required", button = "Payout Locked — Shadow Run Active" (disabled), alert = info explaining no disbursement until post Jun 12, 2026.
- When `false` (post shadow run): original warning alert + enabled "Approve Payout Batch" button.

### Backend: `GET /climate-forecasts/alerts`
- Now excludes forecasts where phenology stage = `off_season`. Prevents August/September drought alerts appearing as active payout triggers.
- `risk_service.py`: added `historicalLossRatio: 0.226` to `/risk/portfolio` response. Used by RiskManagementDashboard for the Actuarial Loss Ratio KPI.
- `types/index.ts`: `PortfolioMetrics` extended with `historicalLossRatio?: number`.
