# From Climate Data to Operational Forecasting: Tanzania Climate Prediction (Part 2 — Shadow Run Pilot)

*By Walter Mnyani*

---

## 📌 Project Overview

In my previous article, I explored how machine learning could be applied to climate data in Tanzania. The goal of that project was to investigate whether historical climate records could be used to identify patterns and generate predictive insights about environmental conditions.

Using historical weather data and machine learning models, the initial results showed that it was possible to capture meaningful relationships within the data. While the project began as an academic exercise, it raised an important question:

*Could these techniques eventually be developed into a practical forecasting system capable of supporting real-world decision making?*

This second phase of the project focuses on moving in that direction — building the infrastructure required for continuous climate forecasting. This includes expanding the dataset, strengthening the modeling framework, and developing an automated pipeline capable of generating daily predictions for a specific community: 1,000 rice farmers in the Kilombero Basin, Morogoro, Tanzania.

The longer-term goal is to support **parametric insurance** — a form of agricultural insurance where payouts are triggered automatically when an environmental index (such as rainfall or temperature) crosses a defined threshold, rather than requiring farmers to file individual claims. For this to work reliably, the forecasting system needs to be accurate, transparent, and verifiable under real-world conditions — which is exactly what this phase sets out to demonstrate.

A key milestone in this phase is the launch of a **Shadow Run**, where the system produces forecasts automatically while the predictions are logged and later compared against real-world outcomes. This forward-testing process allows the forecasting system to be evaluated under realistic conditions before any real financial decision depends on it.

Together, these developments mark an important transition in the project — from a research prototype toward a system designed to operate in real-world environments.

---

## 📊 Exploratory Data Analysis

Before launching the forecasting pipeline, I revisited and extended the exploratory data analysis from the first phase. The goal was to confirm that the climate variables being used capture meaningful environmental signals related to multiple climate risks.

Rather than relying on a single dataset, the project integrates several sources of environmental data that provide complementary perspectives on climate conditions.

**Data Sources**

- **CHIRPS** — high-resolution rainfall estimates
- **ERA5** — reanalysis atmospheric variables for wider climate context
- **NASA POWER** — temperature and solar radiation
- **MODIS NDVI** — satellite vegetation indices monitoring plant health
- **NOAA Ocean Indices** — large-scale climate patterns (ENSO/IOD)

Combining these datasets allows the model to capture a broader range of environmental signals than rainfall data alone.

**Key observations from the analysis**

Several patterns identified during exploratory analysis directly informed the modeling strategy.

*Seasonal rainfall concentration:* Rainfall patterns in Tanzania follow strong seasonal cycles. Heavy precipitation is concentrated during defined rainy seasons, increasing the likelihood of flooding in certain regions. Models therefore need to distinguish between normal seasonal patterns and extreme precipitation events.

![Monthly average temperature and rainfall chart showing Long Rains (Mar–May) and Short Rains (Oct–Dec) seasons, with temperature peaking during dry months (Jun–Oct).](monthly_Avg_seasonal.png)
*Long rains (Mar–May) and Short rains (Oct–Dec) are visible as rainfall peaks. Temperature is highest during dry seasons (Jun–Oct).*

*Rainfall accumulation dynamics:* Flood events are often linked to rainfall accumulation across several consecutive days rather than a single storm. Capturing short-term rainfall persistence helps identify conditions where soil saturation and runoff increase rapidly.

*Extended rainfall deficits:* Drought conditions tend to emerge gradually. Long periods of below-average rainfall lead to sustained moisture deficits that compound over weeks and months — a pattern that single-observation snapshots miss entirely.

*Vegetation response to climate variability:* Satellite-derived vegetation indices show clear responses to both drought stress and temperature anomalies, providing useful leading indicators of emerging crop stress.

These observations helped guide the feature engineering strategy used by the forecasting system.

---

## ⚙️ Methodology

The methodology builds on the modeling work from the first article while introducing a more rigorous validation framework.

One of the main challenges in climate time series modeling is **data leakage** — where information from the future accidentally influences model training. If not handled carefully, this can produce models that appear highly accurate on historical data but fail when used in real forecasting scenarios.

In practice, this risk is subtle. My initial models achieved an accuracy that looked impressive on paper — over 98% on historical validation. But a careful audit revealed that a large number of features had been inadvertently derived from the very variable I was trying to predict. For example, features tracking rainfall accumulation over a period that included the prediction date itself. In a real forecasting scenario, those values simply wouldn't exist yet.

To fix this, I built a dedicated review process to identify and remove any target-derived features, reducing the input feature set from 279 candidates down to 83 clean historical and satellite variables. The result was a more honest model with an **R² of 86.7%** — a meaningful drop, but one that reflects genuine predictive capability rather than an artifact of the data construction process.

With this validation framework in place, the forecasting pipeline could then be evaluated under forward-testing conditions during the Shadow Run phase.

---

## 🤖 Model Development

To develop the forecasting system, I trained and evaluated four different models, each representing a different approach to structured environmental and time-series data.

**Random Forest** — an ensemble tree method that builds multiple decision trees and aggregates their predictions. Robust and interpretable; works well with structured tabular features.

**XGBoost (Gradient Boosting)** — a boosting-based method that sequentially corrects prediction errors. Consistently strong on structured climate data and efficient to retrain as new data accumulates.

**LSTM Neural Network** — a recurrent architecture designed to capture temporal dependencies in sequential data. More expressive for long-range patterns, but computationally heavier to train and validate.

**Weighted Ensemble** — a blended model combining predictions from all three, using fixed weights: Random Forest 30%, XGBoost 40%, LSTM 30%.

Each model was trained using the engineered climate features and evaluated using a time-aware validation strategy, ensuring the model only learns from past observations when predicting future conditions.

All four models were able to identify meaningful relationships within the dataset. The ensemble approach combines their complementary strengths, though it is worth noting that the best individual model — XGBoost — achieved a slightly higher accuracy than the ensemble on its own.

The fixed blending weights were chosen deliberately rather than learned from data. For applications where predictions may be scrutinised by external stakeholders, a transparent and fixed blending rule is easier to explain and verify than a model that learns how to combine predictions through its own training process. I treated interpretability as a functional requirement alongside predictive accuracy.

XGBoost was selected as the **primary inference engine** for the Shadow Run phase, with the ensemble serving as a reference model for comparison.

---

## 🧩 Feature Engineering

Environmental hazards typically emerge from patterns over time, not from a single observation. Feature engineering therefore focuses on capturing temporal signals that reflect how climate conditions evolve across three primary risk categories.

**Flood signals** focus on short-term accumulation and intensity:
- Rolling rainfall totals over short time windows (3, 7, and 14 days)
- Consecutive days of heavy rainfall
- Rainfall intensity relative to seasonal averages

**Drought signals** operate over longer horizons:
- Long-window rainfall anomalies (30- and 90-day deficits)
- Extended dry spell duration
- Temperature deviations from seasonal norms

**Crop failure signals** tie environmental conditions to growing stages:
- Rainfall anomalies during key crop development periods
- Temperature extremes during sensitive growth phases
- Vegetation index trends derived from satellite data

Together, these signals give the model the temporal context needed to distinguish between normal climate variability and conditions that warrant a risk flag.

---

## 🗺️ Pipeline Overview

![HewaSense pipeline diagram showing the 5 data sources flowing through feature engineering, model optimization (XGBoost, LSTM, RF ensemble), forecasting and performance logging, to the Evidence Pack Dashboard.](HewaSense_Pipeline_Diagram.png)
*The HewaSense solution workflow — from raw climate data to actionable risk intelligence.*

---

## 🧱 Technical Stack

The project uses a modern data science and web development workflow designed to support both experimentation and operational forecasting.

Key components include:

- **Data processing:** Python-based pipelines, automated feature engineering, multi-source data ingestion
- **Model development:** gradient boosting algorithms, cross-validation with temporal splits, parameter optimisation
- **Backend API:** FastAPI with a PostgreSQL database for storing forecast logs
- **Frontend:** React/TypeScript dashboard for monitoring and reporting
- **Infrastructure:** Dockerised deployment on a remote server with automated scheduling

---

## 🔎 The Shadow Run Phase

The Shadow Run marks the first time the forecasting system will operate continuously outside of the development environment.

Each day at **6:00 AM East Africa Time**, the pipeline automatically:

1. Fetches the latest available climate data from the five source APIs
2. Generates 24 forecasts for the Kilombero Basin — covering drought, flood, and crop stress across two pilot zones (Ifakara TC + Mlimba DC), looking 3 to 6 months ahead (four separate forecast horizons per zone)
3. Logs each forecast with a timestamp so it can later be compared against observed conditions
4. As forecast windows mature, automatically resolves each prediction against real-world climate data and calculates an accuracy score

At this stage, the system has not yet accumulated enough forward data to generate performance insights. The purpose of the Shadow Run is to collect those observations in real time and evaluate how the model behaves when applied to new data over time.

A dedicated **Evidence Pack Dashboard** displays this accumulating record — tracking prediction accuracy, calibration, and false alarm rates as the shadow run progresses. This growing evidence base is what external stakeholders would need to see before the system could support any real financial decision.

---

## 🧠 Why the Shadow Run Matters

Models that perform well during historical testing do not always maintain that performance when applied to new data.

The Shadow Run is designed to test whether the forecasting system can operate reliably under real-world conditions. By generating predictions continuously and comparing them with future outcomes, it becomes possible to evaluate whether the model generalises well or requires further refinement — using actual forward data rather than retrospective statistics.

This distinction matters: historical accuracy tells you how well a model fits the past. Forward validation tells you whether it can actually anticipate the future under changing conditions.

If the system demonstrates consistent performance during forward testing, the next step will be exploring how the forecasting framework could support real-world climate risk monitoring in the Kilombero Basin. If weaknesses appear, the results will guide targeted improvements to data ingestion, feature engineering, or model calibration.

---

## 🚀 Next Steps

Over the next 90 days, the system will run untouched — silently recording its predictions against actual Tanzanian weather.

As this dataset expands, the evaluation will focus on:

- Predictive accuracy across different environmental conditions and seasons
- Stability of probability estimates over time
- Reliability of forecasts across the different forward horizons

The results of the 90-Day Shadow Run will be covered in Part 3 of this series, in June 2026.

---

## 🧾 Conclusion

The hardest part of applied machine learning is not building a model — it is building the evidence that the model works when it counts.

This phase of the project is fundamentally about that challenge. The forecasting pipeline is live. The predictions are being logged. And over the next 90 days, the system will either demonstrate that it can generalise reliably to new, unseen conditions — or reveal exactly where it needs to improve.

Either outcome is useful. One leads toward a system that can eventually support real financial resilience for smallholder farmers in Tanzania. The other leads toward a better understanding of where climate forecasting models struggle under operational conditions.

That is the value of forward validation done properly: the results are honest, because the future hasn't happened yet when the forecasts are made.

*Follow along or read Part 3 in June 2026 — The Results of the 90-Day Shadow Run.*
