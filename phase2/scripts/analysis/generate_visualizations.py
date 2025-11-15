"""
Generate comprehensive visualizations for Tanzania Climate Data
Creates publication-ready plots for EDA and reporting
"""

import sys
import io

# Ensure UTF-8 encoding for console output (Windows compatibility)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10

# Create output directory
output_dir = Path("outputs/visualizations")
output_dir.mkdir(parents=True, exist_ok=True)

# Load data
print("Loading data...")
df = pd.read_csv("outputs/processed/master_dataset.csv")
df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))

print(f"Loaded {len(df)} records from {df['date'].min().strftime('%Y-%m')} to {df['date'].max().strftime('%Y-%m')}")
print(f"Generating visualizations...\n")

# ============================================================================
# 1. TIME SERIES OF KEY CLIMATE VARIABLES
# ============================================================================
print("1. Creating time series plots...")

fig, axes = plt.subplots(4, 1, figsize=(14, 12))
fig.suptitle('Tanzania Climate Variables Time Series (2020-2021)', fontsize=16, fontweight='bold')

# Temperature
axes[0].plot(df['date'], df['temp_mean_c'], 'o-', color='#d62728', linewidth=2, markersize=6)
axes[0].fill_between(df['date'], df['temp_min_c'], df['temp_max_c'], alpha=0.3, color='#d62728')
axes[0].set_ylabel('Temperature (°C)', fontweight='bold')
axes[0].set_title('Mean Temperature (with min/max range)', fontsize=12)
axes[0].grid(True, alpha=0.3)

# Rainfall
axes[1].bar(df['date'], df['rainfall_mm'], color='#1f77b4', alpha=0.7, width=20)
axes[1].axhline(df['rainfall_mm'].mean(), color='red', linestyle='--', label=f'Mean: {df["rainfall_mm"].mean():.1f} mm')
axes[1].set_ylabel('Rainfall (mm)', fontweight='bold')
axes[1].set_title('Monthly Rainfall', fontsize=12)
axes[1].legend()
axes[1].grid(True, alpha=0.3)

# NDVI
axes[2].plot(df['date'], df['ndvi'], 'o-', color='#2ca02c', linewidth=2, markersize=6)
axes[2].axhline(df['ndvi'].mean(), color='red', linestyle='--', label=f'Mean: {df["ndvi"].mean():.3f}')
axes[2].set_ylabel('NDVI', fontweight='bold')
axes[2].set_title('Vegetation Index (NDVI)', fontsize=12)
axes[2].legend()
axes[2].grid(True, alpha=0.3)

# Ocean Indices
ax2 = axes[3]
ax2.plot(df['date'], df['oni'], 'o-', color='#ff7f0e', linewidth=2, markersize=6, label='ONI (ENSO)')
ax2.axhline(0.5, color='red', linestyle='--', alpha=0.5, label='El Niño threshold')
ax2.axhline(-0.5, color='blue', linestyle='--', alpha=0.5, label='La Niña threshold')
ax2.set_ylabel('ONI (°C)', fontweight='bold', color='#ff7f0e')
ax2.tick_params(axis='y', labelcolor='#ff7f0e')
ax2.set_title('Ocean Climate Indices', fontsize=12)
ax2.grid(True, alpha=0.3)

ax2_twin = ax2.twinx()
ax2_twin.plot(df['date'], df['iod'], 's-', color='#9467bd', linewidth=2, markersize=6, label='IOD')
ax2_twin.axhline(0, color='gray', linestyle='-', alpha=0.3)
ax2_twin.set_ylabel('IOD (°C)', fontweight='bold', color='#9467bd')
ax2_twin.tick_params(axis='y', labelcolor='#9467bd')

# Combine legends
lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

axes[3].set_xlabel('Date', fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / '01_time_series.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: 01_time_series.png")
plt.close()

# ============================================================================
# 2. SEASONAL PATTERNS
# ============================================================================
print("2. Creating seasonal pattern plots...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Seasonal Patterns in Tanzania Climate (2020-2021)', fontsize=16, fontweight='bold')

# Monthly averages
monthly_stats = df.groupby('month').agg({
    'temp_mean_c': 'mean',
    'rainfall_mm': 'mean',
    'ndvi': 'mean',
    'humidity_pct': 'mean'
})

month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# Temperature by month
axes[0, 0].bar(range(1, 13), monthly_stats['temp_mean_c'], color='#d62728', alpha=0.7)
axes[0, 0].set_xticks(range(1, 13))
axes[0, 0].set_xticklabels(month_names, rotation=45)
axes[0, 0].set_ylabel('Temperature (°C)', fontweight='bold')
axes[0, 0].set_title('Average Temperature by Month', fontsize=12)
axes[0, 0].grid(True, alpha=0.3, axis='y')

# Rainfall by month
axes[0, 1].bar(range(1, 13), monthly_stats['rainfall_mm'], color='#1f77b4', alpha=0.7)
axes[0, 1].set_xticks(range(1, 13))
axes[0, 1].set_xticklabels(month_names, rotation=45)
axes[0, 1].set_ylabel('Rainfall (mm)', fontweight='bold')
axes[0, 1].set_title('Average Rainfall by Month', fontsize=12)
axes[0, 1].grid(True, alpha=0.3, axis='y')

# NDVI by month
axes[1, 0].bar(range(1, 13), monthly_stats['ndvi'], color='#2ca02c', alpha=0.7)
axes[1, 0].set_xticks(range(1, 13))
axes[1, 0].set_xticklabels(month_names, rotation=45)
axes[1, 0].set_ylabel('NDVI', fontweight='bold')
axes[1, 0].set_title('Average NDVI by Month', fontsize=12)
axes[1, 0].grid(True, alpha=0.3, axis='y')

# Humidity by month
axes[1, 1].bar(range(1, 13), monthly_stats['humidity_pct'], color='#17becf', alpha=0.7)
axes[1, 1].set_xticks(range(1, 13))
axes[1, 1].set_xticklabels(month_names, rotation=45)
axes[1, 1].set_ylabel('Humidity (%)', fontweight='bold')
axes[1, 1].set_title('Average Humidity by Month', fontsize=12)
axes[1, 1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(output_dir / '02_seasonal_patterns.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: 02_seasonal_patterns.png")
plt.close()

# ============================================================================
# 3. CORRELATION HEATMAP
# ============================================================================
print("3. Creating correlation heatmap...")

# Select key variables for correlation
corr_vars = [
    'temp_mean_c', 'temp_max_c', 'temp_min_c', 'rainfall_mm', 
    'humidity_pct', 'solar_rad_wm2', 'ndvi', 'oni', 'iod'
]
available_vars = [v for v in corr_vars if v in df.columns]

corr_matrix = df[available_vars].corr()

# Create figure
fig, ax = plt.subplots(figsize=(12, 10))
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
            square=True, linewidths=1, cbar_kws={"shrink": 0.8},
            vmin=-1, vmax=1, ax=ax)
ax.set_title('Correlation Matrix of Climate Variables', fontsize=16, fontweight='bold', pad=20)

# Rename labels for better readability
label_map = {
    'temp_mean_c': 'Temp Mean',
    'temp_max_c': 'Temp Max',
    'temp_min_c': 'Temp Min',
    'rainfall_mm': 'Rainfall',
    'humidity_pct': 'Humidity',
    'solar_rad_wm2': 'Solar Rad',
    'ndvi': 'NDVI',
    'oni': 'ONI (ENSO)',
    'iod': 'IOD'
}
ax.set_xticklabels([label_map.get(l.get_text(), l.get_text()) for l in ax.get_xticklabels()], rotation=45, ha='right')
ax.set_yticklabels([label_map.get(l.get_text(), l.get_text()) for l in ax.get_yticklabels()], rotation=0)

plt.tight_layout()
plt.savefig(output_dir / '03_correlation_heatmap.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: 03_correlation_heatmap.png")
plt.close()

# ============================================================================
# 4. ENSO IMPACTS
# ============================================================================
print("4. Creating ENSO impact visualizations...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('ENSO (El Niño/La Niña) Impacts on Tanzania Climate', fontsize=16, fontweight='bold')

# Map ENSO phases
enso_map = {-1: 'La Niña', 0: 'Neutral', 1: 'El Niño'}
df['enso_phase_name'] = df['enso_phase'].map(enso_map)

# Rainfall by ENSO phase
rainfall_by_enso = df.groupby('enso_phase_name')['rainfall_mm'].apply(list)
axes[0, 0].boxplot([rainfall_by_enso.get('La Niña', []), 
                     rainfall_by_enso.get('Neutral', []), 
                     rainfall_by_enso.get('El Niño', [])],
                    labels=['La Niña', 'Neutral', 'El Niño'],
                    patch_artist=True)
axes[0, 0].set_ylabel('Rainfall (mm)', fontweight='bold')
axes[0, 0].set_title('Rainfall Distribution by ENSO Phase', fontsize=12)
axes[0, 0].grid(True, alpha=0.3, axis='y')

# Temperature by ENSO phase
temp_by_enso = df.groupby('enso_phase_name')['temp_mean_c'].apply(list)
axes[0, 1].boxplot([temp_by_enso.get('La Niña', []), 
                     temp_by_enso.get('Neutral', []), 
                     temp_by_enso.get('El Niño', [])],
                    labels=['La Niña', 'Neutral', 'El Niño'],
                    patch_artist=True)
axes[0, 1].set_ylabel('Temperature (°C)', fontweight='bold')
axes[0, 1].set_title('Temperature Distribution by ENSO Phase', fontsize=12)
axes[0, 1].grid(True, alpha=0.3, axis='y')

# NDVI by ENSO phase
ndvi_by_enso = df.groupby('enso_phase_name')['ndvi'].apply(list)
axes[1, 0].boxplot([ndvi_by_enso.get('La Niña', []), 
                     ndvi_by_enso.get('Neutral', []), 
                     ndvi_by_enso.get('El Niño', [])],
                    labels=['La Niña', 'Neutral', 'El Niño'],
                    patch_artist=True)
axes[1, 0].set_ylabel('NDVI', fontweight='bold')
axes[1, 0].set_title('Vegetation Health by ENSO Phase', fontsize=12)
axes[1, 0].grid(True, alpha=0.3, axis='y')

# ONI time series with phases
colors = {'La Niña': '#3498db', 'Neutral': '#95a5a6', 'El Niño': '#e74c3c'}
for phase in df['enso_phase_name'].unique():
    phase_data = df[df['enso_phase_name'] == phase]
    axes[1, 1].scatter(phase_data['date'], phase_data['oni'], 
                      label=phase, color=colors.get(phase, 'gray'), s=100, alpha=0.7)

axes[1, 1].axhline(0.5, color='red', linestyle='--', alpha=0.5, label='El Niño threshold')
axes[1, 1].axhline(-0.5, color='blue', linestyle='--', alpha=0.5, label='La Niña threshold')
axes[1, 1].axhline(0, color='gray', linestyle='-', alpha=0.3)
axes[1, 1].set_ylabel('ONI (°C)', fontweight='bold')
axes[1, 1].set_xlabel('Date', fontweight='bold')
axes[1, 1].set_title('ONI Time Series with Phase Classification', fontsize=12)
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / '04_enso_impacts.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: 04_enso_impacts.png")
plt.close()

# ============================================================================
# 5. RAINFALL-VEGETATION RELATIONSHIP
# ============================================================================
print("5. Creating rainfall-vegetation relationship plot...")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Rainfall and Vegetation Relationship', fontsize=16, fontweight='bold')

# Scatter plot with regression line
axes[0].scatter(df['rainfall_mm'], df['ndvi'], c=df['month'], cmap='viridis', 
                s=100, alpha=0.6, edgecolors='black', linewidth=0.5)
z = np.polyfit(df['rainfall_mm'], df['ndvi'], 1)
p = np.poly1d(z)
axes[0].plot(df['rainfall_mm'], p(df['rainfall_mm']), "r--", linewidth=2, 
             label=f'y={z[0]:.4f}x+{z[1]:.3f}')
axes[0].set_xlabel('Rainfall (mm)', fontweight='bold')
axes[0].set_ylabel('NDVI', fontweight='bold')
axes[0].set_title(f'Rainfall vs NDVI (r={df["rainfall_mm"].corr(df["ndvi"]):.3f})', fontsize=12)
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Add colorbar
cbar = plt.colorbar(axes[0].collections[0], ax=axes[0])
cbar.set_label('Month', fontweight='bold')

# Lagged relationship (rainfall leads NDVI)
df_sorted = df.sort_values('date').copy()
df_sorted['rainfall_lag1'] = df_sorted['rainfall_mm'].shift(1)
df_sorted['rainfall_lag2'] = df_sorted['rainfall_mm'].shift(2)

# Plot current vs lagged
valid_data = df_sorted.dropna(subset=['rainfall_lag1', 'ndvi'])
if len(valid_data) > 0:
    axes[1].scatter(valid_data['rainfall_lag1'], valid_data['ndvi'], 
                   c=valid_data['month'], cmap='viridis', s=100, alpha=0.6, 
                   edgecolors='black', linewidth=0.5)
    z_lag = np.polyfit(valid_data['rainfall_lag1'], valid_data['ndvi'], 1)
    p_lag = np.poly1d(z_lag)
    axes[1].plot(valid_data['rainfall_lag1'], p_lag(valid_data['rainfall_lag1']), 
                "r--", linewidth=2, label=f'y={z_lag[0]:.4f}x+{z_lag[1]:.3f}')
    corr_lag = valid_data['rainfall_lag1'].corr(valid_data['ndvi'])
    axes[1].set_xlabel('Rainfall Previous Month (mm)', fontweight='bold')
    axes[1].set_ylabel('NDVI Current Month', fontweight='bold')
    axes[1].set_title(f'Lagged Relationship (r={corr_lag:.3f})', fontsize=12)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    cbar2 = plt.colorbar(axes[1].collections[0], ax=axes[1])
    cbar2.set_label('Month', fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / '05_rainfall_vegetation.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: 05_rainfall_vegetation.png")
plt.close()

# ============================================================================
# 6. DROUGHT AND FLOOD INDICATORS
# ============================================================================
print("6. Creating drought and flood indicator plots...")

fig, axes = plt.subplots(3, 1, figsize=(14, 12))
fig.suptitle('Drought and Flood Risk Indicators', fontsize=16, fontweight='bold')

# Rainfall anomaly
if 'rainfall_anomaly_mm' in df.columns:
    colors_anom = ['red' if x < 0 else 'blue' for x in df['rainfall_anomaly_mm']]
    axes[0].bar(df['date'], df['rainfall_anomaly_mm'], color=colors_anom, alpha=0.7, width=20)
    axes[0].axhline(0, color='black', linestyle='-', linewidth=1)
    axes[0].set_ylabel('Rainfall Anomaly (mm)', fontweight='bold')
    axes[0].set_title('Rainfall Anomaly (Deviation from Climatology)', fontsize=12)
    axes[0].grid(True, alpha=0.3, axis='y')

# SPI (Standardized Precipitation Index)
if 'spi_30day' in df.columns:
    axes[1].plot(df['date'], df['spi_30day'], 'o-', color='#1f77b4', linewidth=2, markersize=6)
    axes[1].axhline(0, color='black', linestyle='-', linewidth=1)
    axes[1].axhline(1, color='green', linestyle='--', alpha=0.5, label='Wet')
    axes[1].axhline(-1, color='orange', linestyle='--', alpha=0.5, label='Dry')
    axes[1].axhline(-2, color='red', linestyle='--', alpha=0.5, label='Severe Drought')
    axes[1].fill_between(df['date'], -2, -1, alpha=0.2, color='orange')
    axes[1].fill_between(df['date'], -3, -2, alpha=0.2, color='red')
    axes[1].set_ylabel('SPI (30-day)', fontweight='bold')
    axes[1].set_title('Standardized Precipitation Index', fontsize=12)
    axes[1].legend(loc='upper right')
    axes[1].grid(True, alpha=0.3)

# VCI (Vegetation Condition Index)
if 'vci' in df.columns:
    axes[2].plot(df['date'], df['vci'], 'o-', color='#2ca02c', linewidth=2, markersize=6)
    axes[2].axhline(50, color='black', linestyle='-', linewidth=1, label='Normal')
    axes[2].axhline(35, color='orange', linestyle='--', alpha=0.5, label='Moderate Stress')
    axes[2].axhline(20, color='red', linestyle='--', alpha=0.5, label='Severe Stress')
    axes[2].fill_between(df['date'], 0, 20, alpha=0.2, color='red')
    axes[2].fill_between(df['date'], 20, 35, alpha=0.2, color='orange')
    axes[2].set_ylabel('VCI', fontweight='bold')
    axes[2].set_xlabel('Date', fontweight='bold')
    axes[2].set_title('Vegetation Condition Index', fontsize=12)
    axes[2].legend(loc='upper right')
    axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / '06_drought_flood_indicators.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: 06_drought_flood_indicators.png")
plt.close()

# ============================================================================
# 7. SUMMARY DASHBOARD
# ============================================================================
print("7. Creating summary dashboard...")

fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
fig.suptitle('Tanzania Climate Data Summary Dashboard (2020-2021)', 
             fontsize=18, fontweight='bold')

# Top row - Key metrics
ax1 = fig.add_subplot(gs[0, :])
ax1.axis('off')

metrics_text = f"""
KEY STATISTICS (2020-2021)

Temperature: {df['temp_mean_c'].mean():.1f}°C (±{df['temp_mean_c'].std():.1f}°C)  |  Range: {df['temp_min_c'].min():.1f}°C to {df['temp_max_c'].max():.1f}°C
Rainfall: {df['rainfall_mm'].mean():.1f} mm/month (±{df['rainfall_mm'].std():.1f} mm)  |  Total: {df['rainfall_mm'].sum():.0f} mm
NDVI: {df['ndvi'].mean():.3f} (±{df['ndvi'].std():.3f})  |  Range: {df['ndvi'].min():.3f} to {df['ndvi'].max():.3f}
ENSO: La Niña dominant ({(df['enso_phase']==-1).sum()} months)  |  ONI: {df['oni'].mean():.2f}°C (±{df['oni'].std():.2f}°C)
IOD: {df['iod'].mean():.2f}°C (±{df['iod'].std():.2f}°C)  |  Mostly Neutral conditions
"""

ax1.text(0.5, 0.5, metrics_text, ha='center', va='center', fontsize=11, 
         family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

# Middle row - Time series
ax2 = fig.add_subplot(gs[1, :])
ax2_twin = ax2.twinx()

ax2.bar(df['date'], df['rainfall_mm'], color='#1f77b4', alpha=0.5, width=20, label='Rainfall')
ax2.set_ylabel('Rainfall (mm)', fontweight='bold', color='#1f77b4')
ax2.tick_params(axis='y', labelcolor='#1f77b4')

ax2_twin.plot(df['date'], df['ndvi'], 'o-', color='#2ca02c', linewidth=2, markersize=6, label='NDVI')
ax2_twin.set_ylabel('NDVI', fontweight='bold', color='#2ca02c')
ax2_twin.tick_params(axis='y', labelcolor='#2ca02c')

ax2.set_title('Rainfall and Vegetation Index Over Time', fontsize=12, fontweight='bold')
ax2.grid(True, alpha=0.3)

lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

# Bottom row - Distribution plots
ax3 = fig.add_subplot(gs[2, 0])
ax3.hist(df['temp_mean_c'], bins=10, color='#d62728', alpha=0.7, edgecolor='black')
ax3.set_xlabel('Temperature (°C)', fontweight='bold')
ax3.set_ylabel('Frequency', fontweight='bold')
ax3.set_title('Temperature Distribution', fontsize=11)
ax3.grid(True, alpha=0.3, axis='y')

ax4 = fig.add_subplot(gs[2, 1])
ax4.hist(df['rainfall_mm'], bins=10, color='#1f77b4', alpha=0.7, edgecolor='black')
ax4.set_xlabel('Rainfall (mm)', fontweight='bold')
ax4.set_ylabel('Frequency', fontweight='bold')
ax4.set_title('Rainfall Distribution', fontsize=11)
ax4.grid(True, alpha=0.3, axis='y')

ax5 = fig.add_subplot(gs[2, 2])
ax5.hist(df['ndvi'], bins=10, color='#2ca02c', alpha=0.7, edgecolor='black')
ax5.set_xlabel('NDVI', fontweight='bold')
ax5.set_ylabel('Frequency', fontweight='bold')
ax5.set_title('NDVI Distribution', fontsize=11)
ax5.grid(True, alpha=0.3, axis='y')

plt.savefig(output_dir / '07_summary_dashboard.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: 07_summary_dashboard.png")
plt.close()

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("VISUALIZATION GENERATION COMPLETE")
print("="*80)
print(f"\nGenerated 7 visualization files in: {output_dir}")
print("\nFiles created:")
print("  1. 01_time_series.png - Time series of all key variables")
print("  2. 02_seasonal_patterns.png - Monthly averages and patterns")
print("  3. 03_correlation_heatmap.png - Variable correlations")
print("  4. 04_enso_impacts.png - ENSO phase impacts on climate")
print("  5. 05_rainfall_vegetation.png - Rainfall-NDVI relationships")
print("  6. 06_drought_flood_indicators.png - Risk indicators")
print("  7. 07_summary_dashboard.png - Overall summary dashboard")
print("\nAll visualizations saved successfully!")
