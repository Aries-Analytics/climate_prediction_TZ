import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import math
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.forecast_log import ForecastLog
from app.models.climate_data import ClimateData

logger = logging.getLogger(__name__)

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

                # Determine if a trigger condition was met based on threshold
                threshold = float(log.threshold_used) if log.threshold_used else 150.0
                
                if log.forecast_type.upper() == "DROUGHT":
                    actual_outcome = 1 if observed_rainfall < threshold else 0
                elif log.forecast_type.upper() == "EXCESS_RAINFALL":
                    actual_outcome = 1 if observed_rainfall > threshold else 0
                else:
                    actual_outcome = 1 if observed_rainfall < threshold else 0
                
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
            threshold = float(log.threshold_used) if log.threshold_used else 150.0

            if log.forecast_type.upper() == "DROUGHT":
                actual_outcome = 1 if obs_rain < threshold else 0
            else:
                actual_outcome = 1 if obs_rain > threshold else 0

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
