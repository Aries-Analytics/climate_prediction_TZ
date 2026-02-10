"""
Generate Dashboard JSON Report
==============================

Converts the daily phase-based backtest results (CSV) into the JSON format
expected by the RiskManagementDashboard (BacktestingValidation component).

Input: outputs/evaluation/phase_based_backtest_results_daily.csv
Output: outputs/evaluation/simulation_5_report.json
"""

import pandas as pd
import json
import os
from datetime import datetime

# Configuration
INPUT_CSV = 'outputs/evaluation/phase_based_backtest_results_daily.csv'
OUTPUT_JSON = 'outputs/evaluation/simulation_5_report.json'

# Simulation Parameters
FARMER_COUNT = 1000
PREMIUM_PER_FARMER = 91.0
LOCATION_NAME = "Kilombero Basin (Multi-Site)"
CROP_TYPE = "Rice (Phase-Based)"

# External Validation Sources (same as in backtesting_service.py)
KNOWN_EVENTS = {
    2016: {"type": "drought", "source": "FEWS NET", "notes": "East Africa drought"},
    2017: {"type": "drought", "source": "WFP Report", "notes": "Prolonged dry spell"},
    2019: {"type": "flood", "source": "OCHA", "notes": "Heavy rains, flooding"},
    2020: {"type": "flood", "source": "Tanzania Met", "notes": "Above-normal rainfall"},
    2021: {"type": "drought", "source": "FEWS NET", "notes": "Failed long rains"},
    2023: {"type": "flood", "source": "News Reports", "notes": "El Niño flooding"}
}

def generate_json():
    if not os.path.exists(INPUT_CSV):
        print(f"Error: Input file {INPUT_CSV} not found.")
        return

    df = pd.read_csv(INPUT_CSV)
    
    # Calculate Aggregates
    years = sorted(df['year'].unique())
    total_years = len(years)
    total_premiums = FARMER_COUNT * PREMIUM_PER_FARMER * total_years
    total_payouts = df['moderate_payout'].sum() * FARMER_COUNT # CSV payout is per farmer? 
    # Check CSV content: "moderate_payout" is per farmer (e.g., 60.0, 75.0)
    
    loss_ratio = (total_payouts / total_premiums) * 100 if total_premiums > 0 else 0
    total_triggers = df[df['moderate_payout'] > 0].shape[0]  # Number of location-years triggered? 
    # Actually, dashboard expects "Triggers" as events. 
    # If 6 locations trigger in 1 year, is that 6 triggers or 1?
    # The dashboard seems to group by year. "yearly_analysis[year].triggers"
    
    # Let's group by Year to create the yearly_analysis
    yearly_analysis = {}
    
    for year in years:
        year_df = df[df['year'] == year]
        
        # Find if any location triggered in this year
        triggers_list = []
        year_payout_per_farmer = 0
        
        # We process each row (location-year)
        for _, row in year_df.iterrows():
            if row['moderate_payout'] > 0:
                # Add a trigger event
                # Inspect 'triggers' column (e.g., "drought_vegetative")
                trigger_types = row['triggers'].split(', ')
                for t_type in trigger_types:
                    # Clean up trigger type
                    t_clean = t_type.replace(" (Triggered)", "").strip()
                    
                    # External validation check
                    validated = "pending"
                    ext_val = None
                    known = KNOWN_EVENTS.get(year)
                    
                    # Simple matching logic
                    if known:
                        if "drought" in t_clean.lower() and known['type'] == 'drought':
                            validated = "confirmed"
                            ext_val = f"{known['source']}: {known['notes']}"
                        elif "flood" in t_clean.lower() and known['type'] == 'flood':
                            validated = "confirmed"
                            ext_val = f"{known['source']}: {known['notes']}"
                    
                    triggers_list.append({
                        "year": int(year),
                        "month": 3, # Approximate for dashboard
                        "trigger_type": t_clean,
                        "severity": "severe" if row['moderate_payout'] > 60 else "moderate",
                        "observed_value": 0, # Not in CSV summary
                        "threshold_value": 0,
                        "total_payout": row['moderate_payout'] * FARMER_COUNT / len(trigger_types), # Split payout?
                        "validated": validated,
                        "external_validation": ext_val
                    })
                
                year_payout_per_farmer += row['moderate_payout']
        
        # Consolidate payouts for the year (average across locations or sum? 
        # Simulation is usually 1 location portfolio. 
        # Here we simulated 6 locations. Let's average the payout per farmer to represent "A farmer in the basin"
        avg_payout_per_farmer = year_df['moderate_payout'].mean()
        total_year_payout = avg_payout_per_farmer * FARMER_COUNT
        
        yearly_analysis[str(year)] = {
            "triggers": triggers_list,
            "total_payout": total_year_payout,
            "validated": any(t['validated'] == 'confirmed' for t in triggers_list)
        }

    # Recalculate Totals based on the "Basin Average" approach
    # Total Payouts = Sum of yearly total payouts
    total_payouts_basin = sum(y['total_payout'] for y in yearly_analysis.values())
    loss_ratio_basin = (total_payouts_basin / total_premiums) * 100
    
    # Sustainability Recommendation
    if loss_ratio_basin < 60:
        sus_status = "Sustainable"
        rec = "Excellent - Premium may be too high, consider reduction"
    elif loss_ratio_basin < 80:
        sus_status = "Sustainable"
        rec = "Good - Sustainable with adequate reserves"
    else:
        sus_status = "Unsustainable"
        rec = "Unsustainable - Immediate premium adjustment required"

    # Executive Summary matches ValidationReport interface
    report = {
        "title": f"Phase-Based Model Validation: {LOCATION_NAME}",
        "generated_at": datetime.utcnow().isoformat(),
        "executive_summary": {
            "location": LOCATION_NAME,
            "period": f"{min(years)} - {max(years)}",
            "farmers_simulated": FARMER_COUNT,
            "crop": CROP_TYPE,
            "total_triggers": sum(len(y['triggers']) for y in yearly_analysis.values()),
            "total_payouts": round(total_payouts_basin, 2),
            "loss_ratio": round(loss_ratio_basin, 2),
            "sustainability": rec
        },
        "yearly_analysis": yearly_analysis,
        "sustainability_analysis": {
            "loss_ratio": round(loss_ratio_basin, 2),
            "is_sustainable": bool(loss_ratio_basin < 80),
            "recommendation": rec
        },
        "external_validation": {
            "sources": ["FEWS NET", "WFP", "TMA"],
            "validated_events": sum(1 for y in yearly_analysis.values() if y['validated']),
            "total_events": len(years) # Or sum of triggers
        },
        "methodology": {
            "data_sources": ["NASA POWER Daily Data"],
            "trigger_types": ["Drought", "Flood", "Excess Rain"],
            "payout_model": "Phase-Based Dynamic Coverage"
        }
    }
    
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(report, f, indent=2)
        
    print(f"Successfully generated dashboard JSON: {OUTPUT_JSON}")

if __name__ == "__main__":
    generate_json()
