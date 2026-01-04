# Tanzania Climate Prediction - Dashboard Features Summary
**Date**: January 1, 2026  
**Status**: ✅ Active & Deployed

---

## 1. Access & Roles (New)
**Focus**: Role-Based Access Control (RBAC)

To ensure appropriate access to sensitive financial and risk data, the dashboard now enforces strict role-based access.

- **Manager Role (New)**: 
  - Explicitly required to access the **Risk Management** dashboard.
  - Replaces the legacy "viewer" role which lacked sufficient permissions.
  - **Credentials**: `manager@climate-insurance.tz` (See `GETTING_STARTED.md` for passwords).
- **Admin/Analyst**: Retain full access to Model Performance and Climate Insights.

---

## 2. Model Performance Dashboard
**Focus**: Machine Learning Model Evaluation & Transparency

This dashboard provides a transparent view of how the climate prediction models are performing, with a focus on scientific validity and temporal integrity.

### Key Features
- **Temporal Leakage Prevention Visualization**:
  - Explicitly shows the strict temporal ordering enforced between **Training (2000-2018)**, **Validation (2018-2021)**, and **Test (2022-2025)** sets.
  - **Data Splits**: Train (1,090 samples), Validation (230 samples), Test (240 samples).
  - Validates that no future data leaks into training, ensuring realistic performance estimates.

- **Metric Transparency**:
  - **Primary Metrics**: R² (Coefficient of Determination), RMSE (Root Mean Square Error), and MAE (Mean Absolute Error).
  - **Contextual Thresholds**: Color-coded indicators (Green for R² ≥ 0.85) to help users interpret "Good" vs "Excellent" performance in a climate context.
  - **Publication-Ready Confidence**: Displays 95% Confidence Intervals and Standard Deviations for Cross-Validation metrics.
  - **Baseline Comparison**: Benchmarks complex models (XGBoost, Random Forest) against simple baselines (Ridge Regression, Persistence, Mean) to prove value added.

- **Data Quality Indicators**:
  - Displays the **Feature-to-Sample Ratio** (currently **12.82:1**), confirming robust statistical validity (target > 10:1).
  - Detailed breakdown of sample counts across splits.

- **Interactive Visualizations**:
  - **Observed vs Predicted**: Time series view of model predictions against actual ground truth.
  - **Feature Importance**: Bar charts with gradient coloring (light to dark blue) identifying top climate drivers. Includes detailed tooltips with exact importance values.

---

## 2. Climate Insights Dashboard
**Focus**: Exploratory Data Analysis & Trend Identification

This dashboard enables deep-dive analysis of historical climate data, helping insurers and policymakers understand long-term trends and risks.

### Key Features

#### A. Interactive Time Series Analysis
- **Filter Persistence (New)**: Time range selections (e.g., "10 Years") now **persist** when toggling variables. Users don't lose their zoomed-in view when adding/removing data series.
- **Decoupled Filtering (New)**: The variable selector at the top **only** affects the main time series chart. It does **not** hide the statistical deep-dive charts below. This allows users to declutter the main view while keeping access to all statistical summaries.
- **Dynamic Zoom & Pan**: `fixedrange` logic ensures users don't accidentally get lost in empty space, while range selector buttons provide quick navigation.
- **Visual Improvements**: Legend positioned below chart to prevent blocking data; optimized chart heights (450px) for visibility.

#### B. Statistical Distributions
- **Box Plots (Temperature & Rainfall)**:
  - Displays the spread, median (Q2), and outliers for climate variables.
  - Helps identify **extreme months** (outliers) that might trigger insurance payouts.
  - **Always Visible**: These remain visible even if the variable is deselected from the main chart, ensuring context is never lost.

#### C. Seasonal Analysis
- **Monthly Averages Chart**:
  - Aggregates data by month (Jan-Dec) to reveal core seasonal patterns (e.g., Long Rains "Masika" vs Short Rains "Vuli").
  - Critical for identifying shifts in seasonality.

#### D. Advanced Analytics
- **Trend Detection (Rolling Averages)**:
  - 12-month sliding window analysis to smooth out noise and reveal long-term warming or drying trends.
- **Extreme Events Histograms**:
  - visualizing the "Tail Risk". Shows the frequency of extreme high temperatures or heavy rainfall events.
  - Directly maps to **Parametric Insurance Triggers** (e.g., 95th percentile events).
- **Variable Relationships (Scatter Plot)**:
  - Plots Temperature vs Rainfall to identify compound risk scenarios (e.g., "Hot & Dry" drought conditions vs "Cool & Wet" flood risks).

---

## 3. Technical Implementation Details
- **Frontend Stack**: React, TypeScript, Material-UI (MUI), Plotly.js.
- **State Management**: Complex state logic handles the decoupling of visual filters vs data availability.
- **Performance**: Charts use optimized rendering configurations (`scrollZoom: false` to prevent page scroll blocking).

---
*This document serves as the current source of truth for dashboard capabilities as of Jan 2026.*
