"""
Backfill NDVI Observations for Shadow Run Valid Run-Days

Fetches Kilombero MODIS NDVI from GEE for all past valid run-days that
don't yet have an ndvi_observations row, then inserts them as backfilled records.

Usage (inside backend container):
    python scripts/backfill_ndvi_observations.py

Options:
    --dry-run       Print dates to backfill without querying GEE or writing to DB
    --recompute-baseline
                    Re-fetch 2015-2024 Kilombero NDVI from GEE and overwrite the
                    cached baseline JSON before backfilling. Use this on first run
                    or if you suspect the default baseline is off.

The script is idempotent: dates that already have ndvi_observations rows are
skipped. Safe to re-run.
"""
import argparse
import logging
import sys
from datetime import date

# ── Bootstrap path so imports resolve inside the container ────────────────────
sys.path.insert(0, "/app")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_valid_run_days(db) -> list[date]:
    """
    Query forecast_logs for all distinct run dates (valid run-days).
    These are the dates we need NDVI observations for.
    """
    from sqlalchemy import text
    rows = db.execute(
        text("SELECT DISTINCT DATE(issued_at AT TIME ZONE 'Africa/Dar_es_Salaam') AS run_date "
             "FROM forecast_logs ORDER BY run_date")
    ).fetchall()
    return [r[0] for r in rows]


def get_already_backfilled(db) -> set[date]:
    """Return set of run_dates already in ndvi_observations."""
    from sqlalchemy import text
    rows = db.execute(
        text("SELECT run_date FROM ndvi_observations")
    ).fetchall()
    return {r[0] for r in rows}


def main():
    parser = argparse.ArgumentParser(description="Backfill NDVI observations for shadow run")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print dates to backfill, no GEE queries or DB writes")
    parser.add_argument("--recompute-baseline", action="store_true",
                        help="Re-fetch 2015-2024 Kilombero baseline from GEE before backfilling")
    args = parser.parse_args()

    # ── DB session ─────────────────────────────────────────────────────────────
    from app.core.database import SessionLocal
    db = SessionLocal()

    try:
        valid_run_days = get_valid_run_days(db)
        already_done = get_already_backfilled(db)
        to_backfill = [d for d in valid_run_days if d not in already_done]

        logger.info(f"Valid run-days in forecast_logs : {len(valid_run_days)}")
        logger.info(f"Already in ndvi_observations   : {len(already_done)}")
        logger.info(f"To backfill                    : {len(to_backfill)}")

        if not to_backfill:
            logger.info("Nothing to backfill — all valid run-days already have NDVI observations.")
            return

        if args.dry_run:
            logger.info("DRY RUN — dates that would be backfilled:")
            for d in to_backfill:
                logger.info(f"  {d}")
            return

        # ── Optionally recompute baseline ──────────────────────────────────────
        from app.services.ndvi_proxy import (
            compute_and_cache_baseline,
            collect_ndvi_observation,
            _load_baseline,
        )

        if args.recompute_baseline:
            logger.info("Recomputing Kilombero historical baseline (2015-2024) from GEE...")
            baseline = compute_and_cache_baseline(start_year=2015, end_year=2024)
            logger.info(f"Baseline computed: {baseline}")
        else:
            baseline = _load_baseline()
            logger.info(f"Using baseline: {baseline}")

        # ── Backfill each date ─────────────────────────────────────────────────
        succeeded = []
        failed = []

        for run_date in to_backfill:
            logger.info(f"─── Backfilling {run_date} ───")
            try:
                obs = collect_ndvi_observation(
                    db=db,
                    run_date=run_date,
                    is_backfilled=True,
                    baseline=baseline,
                )
                logger.info(
                    f"  ✓ {run_date}: ndvi={obs.ndvi_mean} "
                    f"anomaly={obs.ndvi_anomaly} "
                    f"observed_date={obs.observed_date} "
                    f"coverage={obs.pixel_coverage}%"
                )
                succeeded.append(run_date)
            except Exception as e:
                logger.error(f"  ✗ {run_date}: {e}")
                failed.append((run_date, str(e)))

        # ── Summary ───────────────────────────────────────────────────────────
        logger.info("=" * 60)
        logger.info(f"Backfill complete: {len(succeeded)} succeeded, {len(failed)} failed")
        if failed:
            logger.warning("Failed dates:")
            for d, err in failed:
                logger.warning(f"  {d}: {err}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
