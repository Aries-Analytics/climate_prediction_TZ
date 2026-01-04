# Parametric Insurance Dashboard Metrics & Alignment

**Supporting Document for**: [PARAMETRIC_INSURANCE_FINAL.md](./PARAMETRIC_INSURANCE_FINAL.md)  
**Date**: January 1, 2026

---

## Overview

This document acts as the interpretative guide for the **Trigger Events Dashboard**. It validates how the operational metrics displayed on the dashboard directly correspond to the actuarial and business logic defined in the main Parametric Insurance documentation.

The dashboard serves as the **operational monitor** for the **actuarial model**, translating static policy rules into real-time financial tracking.

---

## 1. Total Financial Exposure
**Dashboard Metric**: Sum of Payout Amounts for all active triggers.

### Alignment with Business Logic
*   **Source Logic**: This is the direct realization of the **Payout Model** (Section 2 of main doc), which defines fixed liabilities: **$60 (Drought)**, **$75 (Flood)**, and **$90 (Crop Failure)**.
*   **Business Impact**: This metric tracks the **Loss Ratio** (Section 3).
    *   **Target**: The sustainable target is a **75% Loss Ratio** (paying out $0.75 for every $1.00 collected).
    *   **Risk Indicator**: If "Total Financial Exposure" exceeds 75% of total collected premiums, the program is entering the "Downside Risk" scenario (Section 8), signaling a threat to financial sustainability.

---

## 2. Trigger Frequency
**Dashboard Metric**: Count of valid trigger events over the selected period.

### Alignment with Business Logic
*   **Source Logic**: Validates the **Historical Performance & Calibration** (Section 2 & 7). The pricing model ($10/year premium) implies specific event probabilities: **Drought (12.0%)**, **Flood (9.3%)**, and **Crop Failure (6.2%)**.
*   **Business Impact**: This metric helps identify **Model Drift**.
    *   **Scenario**: The model expects ~23.5 events/year (Historical Avg). If the dashboard shows significantly more (e.g., >40), it indicates the model is under-pricing risk, potentially due to climate change acceleration (Risk #2).
    *   **Action**: Significant deviation triggers the **Annual Recalibration** process referenced in Section 8.

---

## 3. Avg. Event Severity
**Dashboard Metric**: Average magnitude (0.0 - 1.0) of triggered events.

### Alignment with Business Logic
*   **Source Logic**: Relates to **Trigger Calibration & Threshold Sensitivity** (Section 7). While the payout is fixed (Section 5), the trigger activation depends on exceeding severity thresholds (e.g., SPI < -0.60).
*   **Business Impact**: This measures **Basis Risk** (the mismatch between index and actual loss).
    *   **Low Severity (e.g., ~51%)**: Events are barely crossing the threshold. A high frequency of low-severity events suggests "noise" or overly sensitive thresholds, causing "False Positives" and wasting funds.
    *   **High Severity (e.g., >85%)**: Events are catastrophic. This confirms triggers are capturing true disasters, validating the "insurable interest" and proving value to the farmer ("True Positives").
