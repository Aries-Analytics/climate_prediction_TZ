"""
Exploratory Data Analysis (EDA) for Master Climate Dataset
Generates comprehensive visualizations and statistical summaries
"""

import io
import sys

# Ensure UTF-8 encoding for console output (Windows compatibility)
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")

# Set style
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["font.size"] = 10

# Create output directory for visualizations
VIZ_DIR = Path("outputs/visualizations")
VIZ_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("EXPLORATORY DATA ANALYSIS - Tanzania Climate Master Dataset")
print("=" * 80)

# Load master dataset
print("\n[1/10] Loading master dataset...")
df = pd.read_csv("outputs/processed/master_dataset.csv")
print(f"✓ Loaded {len(df)} rows × {len(df.columns)} columns")
print(f"✓ Date range: {df['year'].min()}-{df['year'].max()}")

# Basic info
print("\n[2/10] Dataset Overview...")
print(f"Shape: {df.shape}")
print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
print(f"\nMissing values:")
missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(2)
missing_df = pd.DataFrame({"Count": missing[missing > 0], "Percentage": missing_pct[missing > 0]})
if len(missing_df) > 0:
    print(missing_df.head(10))
else:
    print("No missing values!")

# Key variables for analysis
key_vars = {
    "rainfall_mm": "Rainfall (mm)",
    "ndvi": "NDVI",
    "temp_mean_c": "Temperature (°C)",
    "oni": "ONI (ENSO)",
    "iod": "IOD",
    "humidity_pct": "Humidity (%)",
}

# Statistical summary
print("\n[3/10] Statistical Summary of Key Variables...")
summary_stats = df[list(key_vars.keys())].describe()
print(summary_stats)

# Save summary
summary_stats.to_csv(VIZ_DIR / "summary_statistics.csv")
print(f"✓ Saved to {VIZ_DIR / 'summary_statistics.csv'}")

# 1. Time Series Plots
print("\n[4/10] Generating time series visualizations...")
df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))

fig, axes = plt.subplots(3, 2, figsize=(15, 12))
fig.suptitle("Time Series of Key Climate Variables (2000-2023)", fontsize=16, fontweight="bold")

for idx, (var, label) in enumerate(key_vars.items()):
    row = idx // 2
    col = idx % 2
    ax = axes[row, col]

    if var in df.columns:
        ax.plot(df["date"], df[var], linewidth=0.8, alpha=0.7)
        ax.set_title(label, fontweight="bold")
        ax.set_xlabel("Year")
        ax.set_ylabel(label)
        ax.grid(True, alpha=0.3)

        # Add trend line
        z = np.polyfit(range(len(df[var].dropna())), df[var].dropna(), 1)
        p = np.poly1d(z)
        ax.plot(df["date"], p(range(len(df))), "r--", alpha=0.5, linewidth=2, label="Trend")
        ax.legend()

plt.tight_layout()
plt.savefig(VIZ_DIR / "01_timeseries_key_variables.png", dpi=300, bbox_inches="tight")
print(f"✓ Saved: 01_timeseries_key_variables.png")
plt.close()

# 2. Seasonal Patterns
print("\n[5/10] Analyzing seasonal patterns...")
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Seasonal Patterns (Monthly Averages)", fontsize=16, fontweight="bold")

seasonal_vars = ["rainfall_mm", "ndvi", "temp_mean_c", "oni"]
for idx, var in enumerate(seasonal_vars):
    ax = axes[idx // 2, idx % 2]
    if var in df.columns:
        monthly_avg = df.groupby("month")[var].mean()
        ax.bar(monthly_avg.index, monthly_avg.values, color="steelblue", alpha=0.7)
        ax.set_title(key_vars.get(var, var), fontweight="bold")
        ax.set_xlabel("Month")
        ax.set_ylabel("Average Value")
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
        ax.grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig(VIZ_DIR / "02_seasonal_patterns.png", dpi=300, bbox_inches="tight")
print(f"✓ Saved: 02_seasonal_patterns.png")
plt.close()

# 3. Correlation Analysis
print("\n[6/10] Computing correlations...")
# Select numeric columns for correlation
numeric_cols = df.select_dtypes(include=[np.number]).columns
# Focus on key variables
focus_vars = [
    "rainfall_mm",
    "ndvi",
    "temp_mean_c",
    "oni",
    "iod",
    "humidity_pct",
    "rainfall_anomaly_mm",
    "ndvi_anomaly",
    "drought_severity",
    "flood_risk_score_left",
]
focus_vars = [v for v in focus_vars if v in df.columns]

corr_matrix = df[focus_vars].corr()

fig, ax = plt.subplots(figsize=(12, 10))
sns.heatmap(
    corr_matrix,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0,
    square=True,
    linewidths=1,
    cbar_kws={"shrink": 0.8},
    ax=ax,
)
ax.set_title("Correlation Matrix of Key Variables", fontsize=14, fontweight="bold", pad=20)
plt.tight_layout()
plt.savefig(VIZ_DIR / "03_correlation_matrix.png", dpi=300, bbox_inches="tight")
print(f"✓ Saved: 03_correlation_matrix.png")
plt.close()

# 4. Distribution Plots
print("\n[7/10] Creating distribution plots...")
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle("Distribution of Key Variables", fontsize=16, fontweight="bold")

for idx, (var, label) in enumerate(key_vars.items()):
    row = idx // 3
    col = idx % 3
    ax = axes[row, col]

    if var in df.columns:
        data = df[var].dropna()
        ax.hist(data, bins=30, color="steelblue", alpha=0.7, edgecolor="black")
        ax.axvline(data.mean(), color="red", linestyle="--", linewidth=2, label=f"Mean: {data.mean():.2f}")
        ax.axvline(data.median(), color="green", linestyle="--", linewidth=2, label=f"Median: {data.median():.2f}")
        ax.set_title(label, fontweight="bold")
        ax.set_xlabel(label)
        ax.set_ylabel("Frequency")
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig(VIZ_DIR / "04_distributions.png", dpi=300, bbox_inches="tight")
print(f"✓ Saved: 04_distributions.png")
plt.close()

# 5. ENSO and IOD Analysis
print("\n[8/10] Analyzing ENSO and IOD patterns...")
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle("ENSO and IOD Climate Patterns", fontsize=16, fontweight="bold")

# ENSO phases over time
if "enso_phase" in df.columns:
    phase_counts = df.groupby(["year", "enso_phase"]).size().unstack(fill_value=0)
    phase_counts.plot(kind="bar", stacked=True, ax=axes[0, 0], color=["red", "blue", "gray"], alpha=0.7)
    axes[0, 0].set_title("ENSO Phases by Year", fontweight="bold")
    axes[0, 0].set_xlabel("Year")
    axes[0, 0].set_ylabel("Number of Months")
    axes[0, 0].legend(title="ENSO Phase")
    axes[0, 0].grid(True, alpha=0.3, axis="y")

# ONI vs Rainfall
if "oni" in df.columns and "rainfall_mm" in df.columns:
    scatter = axes[0, 1].scatter(df["oni"], df["rainfall_mm"], c=df["year"], cmap="viridis", alpha=0.6, s=30)
    axes[0, 1].set_title("ONI vs Rainfall", fontweight="bold")
    axes[0, 1].set_xlabel("ONI (ENSO Index)")
    axes[0, 1].set_ylabel("Rainfall (mm)")
    axes[0, 1].grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=axes[0, 1], label="Year")

# IOD over time
if "iod" in df.columns:
    axes[1, 0].plot(df["date"], df["iod"], linewidth=1, alpha=0.7, color="orange")
    axes[1, 0].axhline(y=0.4, color="r", linestyle="--", alpha=0.5, label="Positive IOD threshold")
    axes[1, 0].axhline(y=-0.4, color="b", linestyle="--", alpha=0.5, label="Negative IOD threshold")
    axes[1, 0].axhline(y=0, color="gray", linestyle="-", alpha=0.3)
    axes[1, 0].set_title("Indian Ocean Dipole (IOD) Over Time", fontweight="bold")
    axes[1, 0].set_xlabel("Year")
    axes[1, 0].set_ylabel("IOD Index")
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

# IOD vs NDVI
if "iod" in df.columns and "ndvi" in df.columns:
    scatter = axes[1, 1].scatter(df["iod"], df["ndvi"], c=df["year"], cmap="viridis", alpha=0.6, s=30)
    axes[1, 1].set_title("IOD vs NDVI", fontweight="bold")
    axes[1, 1].set_xlabel("IOD Index")
    axes[1, 1].set_ylabel("NDVI")
    axes[1, 1].grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=axes[1, 1], label="Year")

plt.tight_layout()
plt.savefig(VIZ_DIR / "05_enso_iod_analysis.png", dpi=300, bbox_inches="tight")
print(f"✓ Saved: 05_enso_iod_analysis.png")
plt.close()

# 6. Drought and Flood Analysis
print("\n[9/10] Analyzing drought and flood indicators...")
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle("Drought and Flood Risk Analysis", fontsize=16, fontweight="bold")

# Drought triggers over time
if "drought_trigger" in df.columns:
    drought_by_year = df.groupby("year")["drought_trigger"].sum()
    axes[0, 0].bar(drought_by_year.index, drought_by_year.values, color="brown", alpha=0.7)
    axes[0, 0].set_title("Drought Triggers by Year", fontweight="bold")
    axes[0, 0].set_xlabel("Year")
    axes[0, 0].set_ylabel("Number of Drought Months")
    axes[0, 0].grid(True, alpha=0.3, axis="y")

# Flood triggers over time
if "flood_trigger" in df.columns:
    flood_by_year = df.groupby("year")["flood_trigger"].sum()
    axes[0, 1].bar(flood_by_year.index, flood_by_year.values, color="blue", alpha=0.7)
    axes[0, 1].set_title("Flood Triggers by Year", fontweight="bold")
    axes[0, 1].set_xlabel("Year")
    axes[0, 1].set_ylabel("Number of Flood Months")
    axes[0, 1].grid(True, alpha=0.3, axis="y")

# Rainfall anomaly over time
if "rainfall_anomaly_mm" in df.columns:
    axes[1, 0].plot(df["date"], df["rainfall_anomaly_mm"], linewidth=0.8, alpha=0.7)
    axes[1, 0].axhline(y=0, color="black", linestyle="-", alpha=0.5)
    axes[1, 0].fill_between(
        df["date"],
        0,
        df["rainfall_anomaly_mm"],
        where=df["rainfall_anomaly_mm"] > 0,
        color="blue",
        alpha=0.3,
        label="Above normal",
    )
    axes[1, 0].fill_between(
        df["date"],
        0,
        df["rainfall_anomaly_mm"],
        where=df["rainfall_anomaly_mm"] < 0,
        color="red",
        alpha=0.3,
        label="Below normal",
    )
    axes[1, 0].set_title("Rainfall Anomaly Over Time", fontweight="bold")
    axes[1, 0].set_xlabel("Year")
    axes[1, 0].set_ylabel("Rainfall Anomaly (mm)")
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

# NDVI anomaly over time
if "ndvi_anomaly" in df.columns:
    axes[1, 1].plot(df["date"], df["ndvi_anomaly"], linewidth=0.8, alpha=0.7, color="green")
    axes[1, 1].axhline(y=0, color="black", linestyle="-", alpha=0.5)
    axes[1, 1].fill_between(
        df["date"], 0, df["ndvi_anomaly"], where=df["ndvi_anomaly"] > 0, color="green", alpha=0.3, label="Above normal"
    )
    axes[1, 1].fill_between(
        df["date"], 0, df["ndvi_anomaly"], where=df["ndvi_anomaly"] < 0, color="brown", alpha=0.3, label="Below normal"
    )
    axes[1, 1].set_title("NDVI Anomaly Over Time", fontweight="bold")
    axes[1, 1].set_xlabel("Year")
    axes[1, 1].set_ylabel("NDVI Anomaly")
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(VIZ_DIR / "06_drought_flood_analysis.png", dpi=300, bbox_inches="tight")
print(f"✓ Saved: 06_drought_flood_analysis.png")
plt.close()

# 7. Extreme Events Summary
print("\n[10/10] Summarizing extreme events...")

# Create summary report
report = []
report.append("=" * 80)
report.append("EXTREME EVENTS SUMMARY (2000-2023)")
report.append("=" * 80)

if "drought_trigger" in df.columns:
    drought_months = df["drought_trigger"].sum()
    drought_years = df[df["drought_trigger"] == 1]["year"].unique()
    report.append(f"\nDROUGHT EVENTS:")
    report.append(f"  Total drought months: {drought_months}")
    report.append(f"  Years with droughts: {len(drought_years)}")
    report.append(f"  Worst drought years: {df.groupby('year')['drought_trigger'].sum().nlargest(5).to_dict()}")

if "flood_trigger" in df.columns:
    flood_months = df["flood_trigger"].sum()
    flood_years = df[df["flood_trigger"] == 1]["year"].unique()
    report.append(f"\nFLOOD EVENTS:")
    report.append(f"  Total flood months: {flood_months}")
    report.append(f"  Years with floods: {len(flood_years)}")
    report.append(f"  Worst flood years: {df.groupby('year')['flood_trigger'].sum().nlargest(5).to_dict()}")

if "enso_phase" in df.columns:
    report.append(f"\nENSO DISTRIBUTION:")
    enso_dist = df["enso_phase"].value_counts()
    for phase, count in enso_dist.items():
        report.append(f"  {phase}: {count} months ({count/len(df)*100:.1f}%)")

if "rainfall_mm" in df.columns:
    report.append(f"\nRAINFALL EXTREMES:")
    report.append(
        f"  Wettest month: {df['rainfall_mm'].max():.2f} mm ({df.loc[df['rainfall_mm'].idxmax(), 'year']}-{df.loc[df['rainfall_mm'].idxmax(), 'month']:02d})"
    )
    report.append(
        f"  Driest month: {df['rainfall_mm'].min():.2f} mm ({df.loc[df['rainfall_mm'].idxmin(), 'year']}-{df.loc[df['rainfall_mm'].idxmin(), 'month']:02d})"
    )

if "ndvi" in df.columns:
    report.append(f"\nVEGETATION EXTREMES:")
    report.append(
        f"  Highest NDVI: {df['ndvi'].max():.4f} ({df.loc[df['ndvi'].idxmax(), 'year']}-{df.loc[df['ndvi'].idxmax(), 'month']:02d})"
    )
    report.append(
        f"  Lowest NDVI: {df['ndvi'].min():.4f} ({df.loc[df['ndvi'].idxmin(), 'year']}-{df.loc[df['ndvi'].idxmin(), 'month']:02d})"
    )

report.append("\n" + "=" * 80)

# Print and save report
report_text = "\n".join(report)
print(report_text)

with open(VIZ_DIR / "extreme_events_summary.txt", "w") as f:
    f.write(report_text)
print(f"\n✓ Saved: extreme_events_summary.txt")

# Final summary
print("\n" + "=" * 80)
print("EDA COMPLETE!")
print("=" * 80)
print(f"\nGenerated visualizations saved to: {VIZ_DIR}/")
print("\nFiles created:")
print("  1. 01_timeseries_key_variables.png")
print("  2. 02_seasonal_patterns.png")
print("  3. 03_correlation_matrix.png")
print("  4. 04_distributions.png")
print("  5. 05_enso_iod_analysis.png")
print("  6. 06_drought_flood_analysis.png")
print("  7. summary_statistics.csv")
print("  8. extreme_events_summary.txt")
print("\n" + "=" * 80)
