import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import math
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.forecast_log import ForecastLog
from app.models.climate_data import ClimateData

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Physical rainfall thresholds for actual-outcome determination (mm / month avg)
#
# The evaluator sums cumulative observed rainfall over the forecast window and
# normalises to a monthly average, then compares against these values.
#
# Source: RAINFALL_THRESHOLDS in rice_thresholds.py (Kilombero rice calendar)
# and calibrated trigger rates in configs/trigger_thresholds.yaml (v2.0.0).
#
# drought    : avg monthly < 80 mm  → event triggered (approx P12 for Kilombero,
#              consistent with 12 % calibrated trigger rate in trigger_thresholds.yaml)
# flood      : avg monthly > 400 mm → event triggered (vegetative-stage "excessive"
#              threshold from RAINFALL_THRESHOLDS; consistent with P95 flood rate)
# heat_stress,
# crop_failure : cannot be evaluated from rainfall alone (require temperature /
#              NDVI / VCI data).  Skip — logs remain "pending" until that data
#              is available (Q2 2026 soil-moisture + NDVI integration roadmap).
# ---------------------------------------------------------------------------
_MONTHLY_DROUGHT_THRESHOLD_MM = 80.0
_MONTHLY_FLOOD_THRESHOLD_MM   = 400.0
_RAINFALL_SKIP_TYPES = {"heat_stress", "crop_failure"}

class ForecastEvaluator:
    """
    Evaluates historical forecasts in the Shadow Run.
    Calculates Predicted vs Actual metrics: Brier Score, RMSE, and Calibration Error.
    """
    
    def __init__(self, db: Session):
        self.db = db

    def backfill_observations(self, logs_to_update: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Manually inject actual observed payload data into specific ForecastLog entries.
        Allows immediate testing of the evaluation engine without waiting for 
        asynchronous climate data ingestion later in the year.
        
        Args:
            logs_to_update: List of dicts, e.g., [{"log_id": "uuid1", "observed_value": 120.5}]
        """
        updated = 0
        errors = 0
        
        for data in logs_to_update:
            try:
                log_id = data.get("log_id")
                obs_val = data.get("observed_value")
                
                if not log_id or obs_val is None:
                    continue
                    
                log_entry = self.db.query(ForecastLog).filter(ForecastLog.id == log_id).first()
                if not log_entry:
                    continue
                    
                log_entry.observed_value = float(obs_val)
                updated += 1
            except Exception as e:
                logger.error(f"Error backfilling log {data.get('log_id')}: {e}")
                errors += 1
                
        self.db.commit()
        return {"updated": updated, "errors": errors}

    def evaluate_pending_forecasts(self) -> Dict[str, Any]:
        """
        Evaluate all 'pending' ForecastLogs where the valid_until date has already passed.
        Compare against observed ClimateData to calculate the Brier Score and update the log.
        """
        now = datetime.now(timezone.utc).date()
        pending_logs = self.db.query(ForecastLog).filter(
            ForecastLog.status == 'pending',
            ForecastLog.valid_until < now
        ).all()

        evaluated_count = 0
        errors = 0

        for log in pending_logs:
            try:
                forecast_type = (log.forecast_type or "").lower()

                # heat_stress and crop_failure require NDVI / temperature data —
                # not available from rainfall alone.  Skip until Q2 2026 integration.
                if forecast_type in _RAINFALL_SKIP_TYPES:
                    continue

                # Retrieve actual cumulative rainfall for the region and time period
                observed_rainfall = self.db.query(func.sum(ClimateData.precipitation)).filter(
                    ClimateData.location_id == int(log.region_id),
                    ClimateData.date >= log.valid_from,
                    ClimateData.date <= log.valid_until
                ).scalar()

                if observed_rainfall is None:
                    # Climate data not yet available for this window
                    continue

                observed_rainfall = float(observed_rainfall)

                # Normalise to average monthly rainfall for the forecast window
                if log.valid_from and log.valid_until:
                    delta_days = (log.valid_until - log.valid_from).days
                    horizon_months = max(1.0, delta_days / 30.0)
                else:
                    horizon_months = max(1.0, (log.lead_time_days or 90) / 30.0)

                avg_monthly_mm = observed_rainfall / horizon_months

                # Determine actual outcome using physical climate thresholds.
                # threshold_used stores the probability trigger level (0.65 / 0.60)
                # and is NOT used here — physical thresholds are defined above.
                if forecast_type == "drought":
                    actual_outcome = 1 if avg_monthly_mm < _MONTHLY_DROUGHT_THRESHOLD_MM else 0
                elif forecast_type in ("flood", "excess_rainfall"):
                    actual_outcome = 1 if avg_monthly_mm > _MONTHLY_FLOOD_THRESHOLD_MM else 0
                else:
                    logger.warning(f"Unknown forecast_type '{log.forecast_type}' for log {log.id}; skipping")
                    continue

                # Brier Score = (predicted_probability - actual_outcome)^2
                predicted_prob = float(log.forecast_value)
                brier_score = (predicted_prob - actual_outcome) ** 2

                # Update the log
                log.observed_value = observed_rainfall
                log.brier_score = round(brier_score, 4)
                log.status = "evaluated"

                evaluated_count += 1
            except Exception as e:
                logger.error(f"Error evaluating forecast {log.id}: {e}")
                errors += 1

        self.db.commit()

        return {
            "processed": evaluated_count,
            "errors": errors,
            "remaining_pending": len(pending_logs) - evaluated_count - errors
        }

    def get_aggregate_metrics(self) -> Dict[str, Any]:
        """
        Calculate Brier Score, RMSE, Calibration Error, and Confusion Matrix 
        across all evaluated ForecastLogs. Provides the dataset for the Evidence Pack.
        """
        evaluated_logs = self.db.query(ForecastLog).filter(
            ForecastLog.status == 'evaluated'
        ).all()

        empty_stats = {
            "brier_score": 0.0,
            "rmse": 0.0,
            "calibration_error": 0.0,
            "total_evaluated": 0,
            "confusion_matrix": {"tp": 0, "fp": 0, "tn": 0, "fn": 0},
            "events": []
        }

        if not evaluated_logs:
            return empty_stats

        brier_scores = []
        predictions = []
        outcomes = []
        events = []
        
        # Confusion matrix counters
        tp, fp, tn, fn = 0, 0, 0, 0
        
        for log in evaluated_logs:
            if log.brier_score is not None:
                brier_scores.append(float(log.brier_score))

            prob = float(log.forecast_value)
            obs_rain = float(log.observed_value) if log.observed_value is not None else 0.0
            forecast_type = (log.forecast_type or "").lower()

            # Normalise observed rainfall to monthly average for threshold comparison
            if log.valid_from and log.valid_until:
                delta_days = (log.valid_until - log.valid_from).days
                horizon_months = max(1.0, delta_days / 30.0)
            else:
                horizon_months = max(1.0, (log.lead_time_days or 90) / 30.0)
            avg_monthly_mm = obs_rain / horizon_months

            if forecast_type == "drought":
                actual_outcome = 1 if avg_monthly_mm < _MONTHLY_DROUGHT_THRESHOLD_MM else 0
            else:
                actual_outcome = 1 if avg_monthly_mm > _MONTHLY_FLOOD_THRESHOLD_MM else 0

            # Confusion Matrix Logic (using 0.5 as the default binary classification threshold)
            predicted_outcome = 1 if prob >= 0.5 else 0
            
            if predicted_outcome == 1 and actual_outcome == 1:
                tp += 1
            elif predicted_outcome == 1 and actual_outcome == 0:
                fp += 1
            elif predicted_outcome == 0 and actual_outcome == 0:
                tn += 1
            elif predicted_outcome == 0 and actual_outcome == 1:
                fn += 1

            predictions.append(prob)
            outcomes.append(actual_outcome)
            events.append({
                "id": log.id,
                "issued_at": log.issued_at.isoformat() if log.issued_at else None,
                "predicted_prob": prob,
                "actual_outcome": actual_outcome,
                "brier_score": float(log.brier_score) if log.brier_score else 0.0
            })

        mean_brier = sum(brier_scores) / len(brier_scores) if brier_scores else 0.0
        rmse = math.sqrt(mean_brier)

        # Calibration Error (Expected Calibration Error - ECE)
        bins = [i / 10.0 for i in range(11)]
        ece = 0.0
        total_preds = len(predictions)
        
        if total_preds > 0:
            for i in range(len(bins) - 1):
                bin_start = bins[i]
                bin_end = bins[i+1]
                
                # Find indices of predictions in this bin
                if i == len(bins) - 2:
                    # Include exact 1.0 in the top bin
                    mask_indices = [idx for idx, p in enumerate(predictions) if bin_start <= p <= bin_end]
                else:
                    mask_indices = [idx for idx, p in enumerate(predictions) if bin_start <= p < bin_end]
                    
                if mask_indices:
                    bin_pred_mean = sum(predictions[idx] for idx in mask_indices) / len(mask_indices)
                    bin_obs_mean = sum(outcomes[idx] for idx in mask_indices) / len(mask_indices)
                    bin_weight = len(mask_indices) / total_preds
                    ece += bin_weight * abs(bin_pred_mean - bin_obs_mean)

        return {
            "brier_score": round(mean_brier, 4),
            "rmse": round(rmse, 4),
            "calibration_error": round(ece, 4),
            "total_evaluated": len(evaluated_logs),
            "confusion_matrix": {
                "tp": tp,
                "fp": fp,
                "tn": tn,
                "fn": fn
            },
            "events": events
        }
