from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import List
from app.models.trigger_event import TriggerEvent

def get_portfolio_metrics(db: Session) -> dict:
    """Calculate portfolio-level risk metrics"""
    # Calculate total exposure
    total_triggers = db.query(func.count(TriggerEvent.id)).scalar() or 0
    total_payouts = db.query(func.sum(TriggerEvent.payout_amount)).scalar() or 0
    
    # Distribution by type
    type_distribution = db.query(
        TriggerEvent.trigger_type,
        func.count(TriggerEvent.id).label('count'),
        func.sum(TriggerEvent.payout_amount).label('total_payout')
    ).group_by(TriggerEvent.trigger_type).all()
    
    distribution = {}
    for trigger_type, count, payout in type_distribution:
        distribution[trigger_type] = {
            "count": count,
            "total_payout": float(payout or 0)
        }
    
    return {
        "total_triggers": total_triggers,
        "total_payouts": float(total_payouts),
        "distribution": distribution,
        "average_payout": float(total_payouts / total_triggers) if total_triggers > 0 else 0
    }

def run_scenario_analysis(db: Session, scenario: dict) -> dict:
    """Run scenario analysis for risk assessment"""
    # This is a simplified version
    # Real implementation would use complex modeling
    
    scenario_type = scenario.get("type", "baseline")
    multiplier = scenario.get("multiplier", 1.0)
    
    # Get current metrics
    current_metrics = get_portfolio_metrics(db)
    
    # Apply scenario multiplier
    projected_triggers = int(current_metrics["total_triggers"] * multiplier)
    projected_payouts = current_metrics["total_payouts"] * multiplier
    
    return {
        "scenario": scenario_type,
        "current_triggers": current_metrics["total_triggers"],
        "projected_triggers": projected_triggers,
        "current_payouts": current_metrics["total_payouts"],
        "projected_payouts": projected_payouts,
        "impact": {
            "trigger_change": projected_triggers - current_metrics["total_triggers"],
            "payout_change": projected_payouts - current_metrics["total_payouts"]
        }
    }

def get_recommendations(db: Session) -> List[dict]:
    """Generate risk management recommendations"""
    metrics = get_portfolio_metrics(db)
    
    recommendations = []
    
    # Check if any trigger type is dominant
    if metrics["distribution"]:
        max_type = max(metrics["distribution"].items(), key=lambda x: x[1]["count"])
        if max_type[1]["count"] / metrics["total_triggers"] > 0.5:
            recommendations.append({
                "priority": "high",
                "category": "diversification",
                "message": f"{max_type[0]} triggers represent over 50% of total triggers",
                "action": "Consider diversifying risk across different trigger types"
            })
    
    # Check average payout
    if metrics["average_payout"] > 10000:
        recommendations.append({
            "priority": "medium",
            "category": "payout_management",
            "message": "Average payout is high",
            "action": "Review payout structures and consider adjusting thresholds"
        })
    
    return recommendations
