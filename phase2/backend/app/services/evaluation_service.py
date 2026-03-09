import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import math
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.forecast_log import ForecastLog
from app.models.climate_data import ClimateData
from app.models.location import Location

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Physical thresholds for actual-outcome determination per forecast type.
#
# drought      : avg monthly rainfall < 80 mm/month → triggered
#                (approx P12 for Kilombero, consistent with 12% calibrated rate
#                in configs/trigger_thresholds.yaml v2.0.0)
#
# flood        : avg monthly rainfall > 400 mm/month → triggered
#                (vegetative-stage "excessive" from rice_thresholds.RAINFALL_THRESHOLDS;
#                consistent with P95 calibrated rate)
#
# heat_stress  : avg temperature over period > 35°C → triggered
#                (sustained monthly avg above 35°C causes spikelet sterility in rice
#                during reproductive stage; standard IRRI threshold)
#
# crop_failure : avg NDVI over period < 0.30 → triggered
#                (NDVI < 0.30 = severely stressed / sparse vegetation;
#                proxy for the calibrated VCI < 3.33 threshold in trigger_thresholds.yaml)
#
# Coordinate tolerance for ClimateData lat/lon queries: ±0.01° (~1.1 km).
# The locations table and climate_data rows use slightly different coordinate
# precision; 0.001° was too tight (missed Morogoro by 0.0039°).
# ---------------------------------------------------------------------------
_MONTHLY_DROUGHT_THRESHOLD_MM  = 80.0
_MONTHLY_FLOOD_THRESHOLD_MM    = 400.0
_HEAT_STRESS_TEMP_C            = 35.0
_CROP_FAILURE_NDVI             = 0.30
_COORD_TOLERANCE               = 0.01   # degrees (~1.1 km)


def _location_filter(location: Location):
    """Return SQLAlchemy filters matching ClimateData rows for a Location."""
    return and_(
        ClimateData.location_lat >= float(location.latitude)  - _COORD_TOLERANCE,
        ClimateData.location_lat <= float(location.latitude)  + _COORD_TOLERANCE,
        ClimateData.location_lon >= float(location.longitude) - _COORD_TOLERANCE,
        ClimateData.location_lon <= float(location.longitude) + _COORD_TOLERANCE,
    )


def _get_actual_outcome(log: ForecastLog, forecast_type: str) -> tuple:
    """
    Returns (actual_outcome: int, observed_value: float) derived from the
    already-stored log.observed_value.  Used in get_aggregate_metrics() where
    data has already been evaluated.
    """
    obs = float(log.observed_value) if log.observed_value is not None else 0.0

    if forecast_type == "drought":
        # observed_value stores cumulative rainfall; normalise to monthly avg
        horizon_months = _horizon_months(log)
        actual_outcome = 1 if (obs / horizon_months) < _MONTHLY_DROUGHT_THRESHOLD_MM else 0
    elif forecast_type in ("flood", "excess_rainfall"):
        horizon_months = _horizon_months(log)
        actual_outcome = 1 if (obs / horizon_months) > _MONTHLY_FLOOD_THRESHOLD_MM else 0
    elif forecast_type == "heat_stress":
        # observed_value stores avg temperature (°C)
        actual_outcome = 1 if obs > _HEAT_STRESS_TEMP_C else 0
    elif forecast_type == "crop_failure":
        # observed_value stores avg NDVI
        actual_outcome = 1 if obs < _CROP_FAILURE_NDVI else 0
    else:
        actual_outcome = 0

    return actual_outcome, obs


def _horizon_months(log: ForecastLog) -> float:
    if log.valid_from and log.valid_until:
        return max(1.0, (log.valid_until - log.valid_from).days / 30.0)
    return max(1.0, (log.lead_time_days or 90) / 30.0)


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
        Evaluate all 'pending' ForecastLogs where the valid_until date has passed.
        Compare against observed ClimateData to calculate Brier Score and update the log.

        Evaluation logic per forecast type:
        - drought / flood     : compare cumulative rainfall (rainfall_mm) vs monthly threshold
        - heat_stress         : compare avg temperature (temperature_avg) vs 35°C
        - crop_failure        : compare avg NDVI (ndvi) vs 0.30
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

                # Look up the Location to get lat/lon for the ClimateData query.
                # region_id stores the integer location PK (e.g. 6 = Morogoro).
                location = self.db.query(Location).filter(
                    Location.id == int(log.region_id)
                ).first()
                if not location:
                    logger.warning(f"Location {log.region_id} not found for log {log.id}; skipping")
                    continue

                loc_filter = _location_filter(location)
                date_filter = and_(
                    ClimateData.date >= log.valid_from,
                    ClimateData.date <= log.valid_until,
                )

                if forecast_type in ("drought", "flood", "excess_rainfall"):
                    # Sum cumulative rainfall over the forecast window
                    observed = self.db.query(func.sum(ClimateData.rainfall_mm)).filter(
                        loc_filter, date_filter
                    ).scalar()
                    if observed is None:
                        continue
                    observed = float(observed)
                    horizon_months = _horizon_months(log)
                    avg_monthly = observed / horizon_months
                    if forecast_type == "drought":
                        actual_outcome = 1 if avg_monthly < _MONTHLY_DROUGHT_THRESHOLD_MM else 0
                    else:
                        actual_outcome = 1 if avg_monthly > _MONTHLY_FLOOD_THRESHOLD_MM else 0

                elif forecast_type == "heat_stress":
                    observed = self.db.query(func.avg(ClimateData.temperature_avg)).filter(
                        loc_filter, date_filter
                    ).scalar()
                    if observed is None:
                        continue
                    observed = float(observed)
                    actual_outcome = 1 if observed > _HEAT_STRESS_TEMP_C else 0

                elif forecast_type == "crop_failure":
                    observed = self.db.query(func.avg(ClimateData.ndvi)).filter(
                        loc_filter, date_filter
                    ).scalar()
                    if observed is None:
                        continue
                    observed = float(observed)
                    actual_outcome = 1 if observed < _CROP_FAILURE_NDVI else 0

                else:
                    logger.warning(f"Unknown forecast_type '{log.forecast_type}' for log {log.id}; skipping")
                    continue

                # Brier Score = (predicted_probability - actual_outcome)^2
                predicted_prob = float(log.forecast_value)
                brier_score = (predicted_prob - actual_outcome) ** 2

                log.observed_value = observed
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

        tp, fp, tn, fn = 0, 0, 0, 0

        for log in evaluated_logs:
            if log.brier_score is not None:
                brier_scores.append(float(log.brier_score))

            prob = float(log.forecast_value)
            forecast_type = (log.forecast_type or "").lower()
            actual_outcome, _ = _get_actual_outcome(log, forecast_type)

            # Confusion matrix (binary classification at 0.5 threshold)
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

        # Expected Calibration Error (ECE)
        bins = [i / 10.0 for i in range(11)]
        ece = 0.0
        total_preds = len(predictions)

        if total_preds > 0:
            for i in range(len(bins) - 1):
                bin_start = bins[i]
                bin_end = bins[i + 1]
                if i == len(bins) - 2:
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
            "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
            "events": events
        }
