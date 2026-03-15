"""
One-time backfill: populate expected_deficit for Forecast records where it is NULL.

Uses the exact same inverse of _raw_to_probability used at forecast creation time:
    _raw_to_probability: prob = CDF((threshold - predicted_mm) / rmse)
    inverse:             predicted_mm = threshold - rmse * ppf(prob)
    deficit:             max(0, threshold - predicted_mm) = max(0, rmse * ppf(prob))

This is not a fabricated estimate — it is a mathematically exact inversion of
the stored probability back to the original threshold-relative deficit.

Run once after deploying the fix that stores expected_deficit going forward.
Safe to re-run (only touches rows where expected_deficit IS NULL).
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scipy.stats import norm
from app.core.database import SessionLocal
from app.models.forecast import Forecast
from app.config.rice_thresholds import RAINFALL_THRESHOLDS, get_kilombero_stage

# Mirror constants from forecast_service.py
_MODEL_RMSE_MM = 33.1

def compute_deficit(trigger_type: str, target_date, probability: float) -> float | None:
    season_type = 'dry' if target_date.month in (7, 8, 9, 10, 11, 12) else 'wet'
    phase = get_kilombero_stage(target_date, season_type)
    thresholds = RAINFALL_THRESHOLDS.get(phase, RAINFALL_THRESHOLDS.get('germination', {}))

    prob_clipped = max(0.001, min(0.999, probability))
    predicted_offset = _MODEL_RMSE_MM * norm.ppf(prob_clipped)  # rmse * ppf(prob)

    if trigger_type == 'drought':
        threshold = thresholds.get('min', 0.0)
        return max(0.0, predicted_offset)           # = max(0, threshold - predicted_mm)
    elif trigger_type == 'flood':
        threshold = thresholds.get('excessive', 0.0)
        return max(0.0, predicted_offset)
    elif trigger_type == 'crop_failure':
        return max(0.0, predicted_offset)
    return None


def run():
    db = SessionLocal()
    try:
        rows = db.query(Forecast).filter(Forecast.expected_deficit.is_(None)).all()
        print(f"Found {len(rows)} Forecast rows with NULL expected_deficit")

        updated = 0
        for f in rows:
            deficit = compute_deficit(f.trigger_type, f.target_date, float(f.probability))
            if deficit is not None:
                f.expected_deficit = round(deficit, 2)
                updated += 1

        db.commit()
        print(f"Backfilled {updated} rows. Done.")
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    run()
