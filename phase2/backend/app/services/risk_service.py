from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date, timedelta
from typing import List, Dict
from app.models.forecast import Forecast
from app.models.location import Location

# Morogoro Pilot Configuration Constants
PILOT_LOCATION_ID = 6
TOTAL_FARMERS = 1000
CURRENT_RESERVES = 150000
PAYOUT_RATES = {
    "drought": 60,
    "flood": 75,
    "crop_failure": 90
}
PREMIUM_PER_FARMER = 20  # Pilot premium: $20/farmer/year (see PARAMETRIC_INSURANCE_FINAL.md Scenario A)
HIGH_RISK_THRESHOLD = 0.75
PRIMARY_HORIZON_MAX = 4  # Months: primary tier (3-4) is insurance-trigger eligible; advisory (5-6) is early warning only


def get_portfolio_metrics(db: Session) -> dict:
    """
    Calculate portfolio-level risk metrics for Morogoro pilot.

    Uses PRIMARY TIER forecasts only (horizon_months <= 4).
    Advisory tier (5-6 months) is early warning only — never triggers a payout.
    Per trigger_type, uses the MAX probability forecast to avoid double-counting
    across horizons (a farmer is paid once per event, not once per forecast row).
    """
    today = date.today()
    horizon_end = today + timedelta(days=180)  # 6-month window

    # Primary tier only: one expected payout per trigger_type at max probability
    best_per_type = db.query(
        Forecast.trigger_type,
        func.max(Forecast.probability).label('max_prob')
    ).filter(
        and_(
            Forecast.location_id == PILOT_LOCATION_ID,
            Forecast.probability >= HIGH_RISK_THRESHOLD,
            Forecast.target_date >= today,
            Forecast.target_date <= horizon_end,
            Forecast.horizon_months <= PRIMARY_HORIZON_MAX
        )
    ).group_by(Forecast.trigger_type).all()

    # Calculate expected payouts
    expected_payouts = 0.0
    trigger_breakdown = {"drought": 0.0, "flood": 0.0, "crop_failure": 0.0}

    for trigger_type, max_prob in best_per_type:
        payout_rate = PAYOUT_RATES.get(trigger_type, 0)
        payout = TOTAL_FARMERS * payout_rate * float(max_prob)
        expected_payouts += payout
        trigger_breakdown[trigger_type] = payout
    
    # Calculate total premium income (annual)
    total_premium_income = TOTAL_FARMERS * PREMIUM_PER_FARMER
    
    # Calculate loss ratio
    # For 6-month period, use half of annual premiums
    six_month_premiums = total_premium_income / 2
    loss_ratio = expected_payouts / six_month_premiums if six_month_premiums > 0 else 0
    
    # Calculate total exposure (worst case: all farmers, all trigger at max)
    total_exposure = TOTAL_FARMERS * max(PAYOUT_RATES.values())
    
    return {
        "totalPremiumIncome": total_premium_income,  # Annual
        "expectedPayouts": round(expected_payouts, 2),  # 6-month projected
        "lossRatio": min(loss_ratio, 2.0),  # Cap at 200% for display
        "numberOfPolicies": TOTAL_FARMERS,
        "totalExposure": total_exposure,
        "reserves": CURRENT_RESERVES,
        "triggerBreakdown": {
            "drought": round(trigger_breakdown["drought"], 2),
            "flood": round(trigger_breakdown["flood"], 2),
            "crop_failure": round(trigger_breakdown["crop_failure"], 2)
        },
        "timeframe": "6-month forecast",
        "pilotLocation": "Morogoro (Location ID 6)",
        "shadowRunConfig": {
            "start": "Mar 7, 2026",
            "end": "Jun 12, 2026",
            "brierEvalDate": "~Jun 9, 2026"
        }
    }


def run_scenario_analysis(db: Session, scenario: dict) -> dict:
    """
    Run scenario analysis for risk assessment
    Simulates impact of climate scenarios on portfolio
    """
    scenario_name = scenario.get("scenarioName", "Unnamed Scenario")
    parameters = scenario.get("parameters", {})
    
    # Get baseline metrics
    baseline = get_portfolio_metrics(db)
    
    # Parse scenario parameters
    rainfall_reduction = parameters.get("rainfall_reduction", 0)  # 0-1 (e.g., 0.3 = 30% reduction)
    temperature_increase = parameters.get("temperature_increase", 0)  # degrees C
    
    # Scenario modeling (Generative + Multiplicative)
    # If baseline is zero, we must GENERATE risk based on physical parameters
    
    # 1. Drought Risk (Driven by Rainfall Reduction)
    # 30% reduction implies significant drought risk (e.g. 50% probability of payout)
    # Formula: Base + (Exposure * Intensity * Sensitivity)
    drought_exposure = TOTAL_FARMERS * PAYOUT_RATES["drought"]
    drought_intensity = min(1.0, rainfall_reduction * 2.5) # 40% reduction = 100% intensity
    new_drought_payout = max(
        baseline["triggerBreakdown"]["drought"] * (1.0 + rainfall_reduction * 3.0),
        drought_exposure * drought_intensity * 0.8 # Cap at 80% of total exposure for pure simulation
    )

    # 2. Flood Risk (Driven by Rainfall INCREASES, modeled here inversely)
    # For this dashboard we simulate reduction mostly, but if rainfall_reduction < 0 (increase), flood risk goes up
    flood_exposure = TOTAL_FARMERS * PAYOUT_RATES["flood"]
    if rainfall_reduction < 0:
        rainfall_increase = abs(rainfall_reduction)
        new_flood_payout = max(
            baseline["triggerBreakdown"]["flood"] * (1.0 + rainfall_increase * 3.0),
            flood_exposure * min(1.0, rainfall_increase * 2.0) * 0.8
        )
    else:
        new_flood_payout = baseline["triggerBreakdown"]["flood"] * (1.0 - rainfall_reduction * 0.5)

    # 3. Crop Failure (Driven by Temperature)
    crop_exposure = TOTAL_FARMERS * PAYOUT_RATES["crop_failure"]
    temp_intensity = min(1.0, temperature_increase / 4.0) # +4C = 100% intensity
    new_crop_payout = max(
        baseline["triggerBreakdown"]["crop_failure"] * (1.0 + temperature_increase * 0.4),
        crop_exposure * temp_intensity * 0.7
    )
    
    scenario_payouts = new_drought_payout + new_flood_payout + new_crop_payout
    
    scenario_loss_ratio = scenario_payouts / (baseline["totalPremiumIncome"] / 2)
    
    # Determine trigger probability (simplified)
    trigger_probability = min(0.95, (scenario_loss_ratio - 0.3) / 1.5)  # Normalize to 0-1
    
    # Impact assessment
    # Impact assessment
    # Fix: Handle zero-baseline case and consider absolute loss ratio
    payout_increase_percent = 0
    if baseline["expectedPayouts"] > 0:
        payout_increase_percent = ((scenario_payouts - baseline["expectedPayouts"]) / baseline["expectedPayouts"] * 100)
    elif scenario_payouts > 0:
        payout_increase_percent = 10000 # Massive increase from zero
    
    # Determine impact based on BOTH relative increase AND absolute severity
    if scenario_loss_ratio > 0.8 or payout_increase_percent > 50:
        impact = "High Impact"
    elif scenario_loss_ratio > 0.6 or payout_increase_percent > 20:
        impact = "Medium Impact"
    else:
        impact = "Low Impact"
    
    return {
        "scenarioName": scenario_name,
        "parameters": parameters,
        "expectedPayouts": round(scenario_payouts, 2),
        "lossRatio": min(scenario_loss_ratio, 2.0),
        "triggerProbability": max(0, min(1.0, trigger_probability)),
        "impact": impact,
        "baseline": {
            "expectedPayouts": baseline["expectedPayouts"],
            "lossRatio": baseline["lossRatio"]
        },
        "change": {
            "payouts": round(scenario_payouts - baseline["expectedPayouts"], 2),
            "payoutsPercent": round(payout_increase_percent, 1)
        }
    }


def get_recommendations(db: Session) -> List[str]:
    """
    Generate risk management recommendations based on forecast data
    Returns simple string recommendations for dashboard display
    """
    metrics = get_portfolio_metrics(db)
    recommendations = []
    
    # Check loss ratio
    if metrics["lossRatio"] > 0.8:
        recommendations.append(
            f"CRITICAL: Loss ratio at {metrics['lossRatio']*100:.1f}% - consider increasing reserves or adjusting coverage"
        )
    elif metrics["lossRatio"] > 0.6:
        recommendations.append(
            f"WARNING: Loss ratio at {metrics['lossRatio']*100:.1f}% - monitor closely and prepare for potential reserve shortfall"
        )
    
    # Check reserves vs expected payouts
    buffer = metrics["reserves"] - metrics["expectedPayouts"]
    buffer_percent = (buffer / metrics["reserves"] * 100) if metrics["reserves"] > 0 else -100
    
    if buffer_percent < 0:
        recommendations.append(
            f"URGENT: Expected payouts (${metrics['expectedPayouts']:,.0f}) exceed reserves (${metrics['reserves']:,.0f}) - secure additional funding immediately"
        )
    elif buffer_percent < 20:
        recommendations.append(
            f"Low buffer: Only {buffer_percent:.1f}% reserve buffer remaining - consider risk mitigation strategies"
        )
    
    # Check trigger concentration
    total_trigger_payout = sum(metrics["triggerBreakdown"].values())
    if total_trigger_payout > 0:
        for trigger_type, payout in metrics["triggerBreakdown"].items():
            if payout / total_trigger_payout > 0.6:
                recommendations.append(
                    f"High concentration: {trigger_type.replace('_', ' ').title()} represents {payout/total_trigger_payout*100:.0f}% of expected payouts"
                )
    
    # Default positive message if all looks good
    if not recommendations:
        recommendations.append(
            f"Portfolio health good: Loss ratio {metrics['lossRatio']*100:.1f}%, adequate reserves with {buffer_percent:.1f}% buffer"
        )
    
    return recommendations
