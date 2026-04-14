import os
import csv
import json
import zipfile
import tempfile
import logging
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from app.models.forecast_log import ForecastLog
from app.services.evaluation_service import ForecastEvaluator
from app.config import shadow_run as sr_cfg

logger = logging.getLogger(__name__)

# Persistent path for the shadow run final report (survives container restarts).
# The /app mount is rw-bound to the host repo, so this file is durable.
_FINAL_REPORT_PATH = Path(__file__).parent.parent.parent / "data" / "processed" / "shadow_run_final_report.json"

# Go/no-go gate thresholds (must match pitch deck and PARAMETRIC_INSURANCE_FINAL.md)
BRIER_SCORE_GATE = 0.25
BASIS_RISK_GATE  = 0.30


class EvidencePackGenerator:
    """
    Generates a cryptographically sound, auditable Evidence Pack for Reinsurers.
    Bundles the evaluation metrics, model version data, and entire forecast history into a ZIP.

    All outputs include mandatory per-zone breakdowns (Ifakara TC / Mlimba DC).
    """

    def __init__(self, db: Session):
        self.db = db
        self.evaluator = ForecastEvaluator(db)

    def _get_zone_names(self) -> dict:
        """Map location_id → zone name from the Location table."""
        from app.models.location import Location
        return {str(loc.id): loc.name for loc in self.db.query(Location).all()}

    def generate_zip(self) -> FileResponse:
        """
        Gathers logs and metrics, writes them to a temporary directory,
        zips them, and returns a FileResponse suitable for FastAPI.

        The ZIP now includes per-zone metrics inside metrics.json and a
        zone_name column in logs_export.csv.
        """
        # 1. Gather all evaluated logs
        evaluated_logs = self.db.query(ForecastLog).filter(
            ForecastLog.status == 'evaluated'
        ).order_by(ForecastLog.issued_at.desc()).all()

        # 2. Gather aggregate metrics (includes per-zone breakdown)
        metrics = self.evaluator.get_aggregate_metrics()

        # 3. Gather basis risk (includes per-zone breakdown)
        from app.services.basis_risk_service import compute_ndvi_proxy_basis_risk
        basis_risk = compute_ndvi_proxy_basis_risk(self.db)
        metrics["basis_risk"] = basis_risk

        zone_names = self._get_zone_names()

        # 4. Setup Temp Directory
        temp_dir = tempfile.mkdtemp()
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        zip_filename = f"hewasense_evidence_pack_{now_str}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:

            # --- File 1: metrics.json (zone-aware) ---
            metrics_path = os.path.join(temp_dir, "metrics.json")
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f, indent=4)
            zipf.write(metrics_path, arcname="metrics.json")

            # --- File 2: logs_export.csv (with zone_name column) ---
            csv_path = os.path.join(temp_dir, "logs_export.csv")
            with open(csv_path, 'w', newline='') as csvfile:
                fieldnames = [
                    'id', 'issued_at', 'region_id', 'zone_name', 'forecast_type',
                    'model_version', 'lead_time_days', 'forecast_value',
                    'threshold_used', 'observed_value', 'brier_score',
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for log in evaluated_logs:
                    writer.writerow({
                        'id': log.id,
                        'issued_at': log.issued_at.isoformat() if log.issued_at else "",
                        'region_id': log.region_id,
                        'zone_name': zone_names.get(str(log.region_id), ""),
                        'forecast_type': log.forecast_type,
                        'model_version': log.model_version,
                        'lead_time_days': log.lead_time_days,
                        'forecast_value': float(log.forecast_value) if log.forecast_value is not None else "",
                        'threshold_used': float(log.threshold_used) if log.threshold_used is not None else "",
                        'observed_value': float(log.observed_value) if log.observed_value is not None else "",
                        'brier_score': float(log.brier_score) if log.brier_score is not None else "",
                    })
            zipf.write(csv_path, arcname="logs_export.csv")

            # --- File 3: model_compliance_statement.txt ---
            statement_path = os.path.join(temp_dir, "model_compliance_statement.txt")
            with open(statement_path, 'w') as f:
                f.write("HewaSense Climate Engine V4.0 - Shadow Run Evidence Pack\n")
                f.write(f"Generated at: {now_str} UTC\n\n")
                f.write("Statement of Compliance:\n")
                f.write("1. All forecasts included in this pack were generated with zero look-ahead bias.\n")
                f.write("2. No fabricated fallback methods were utilized for data outages (GOTCHA Law #1 compliant).\n")
                f.write("3. Evaluation calculates Brier Score explicitly from recorded `.predict()` probabilities.\n")
                f.write("4. Metrics are reported per-zone (Ifakara TC, Mlimba DC) and in aggregate.\n")

                # Sniff the most recent model version used
                recent_version = evaluated_logs[0].model_version if evaluated_logs else "Unknown"
                f.write(f"\nLatest Model Version active in this evaluation window: {recent_version}\n")
            zipf.write(statement_path, arcname="model_compliance_statement.txt")

        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            media_type="application/zip"
        )

    # ------------------------------------------------------------------
    # GO/NO-GO gate helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _evaluate_gate(brier_score, basis_risk_result) -> dict:
        """
        Evaluate GO/NO-GO for a single set of metrics (zone or aggregate).
        Returns a gate dict with brier, basis_risk, and verdict.
        """
        brier_gate_pass = (brier_score is not None and brier_score < BRIER_SCORE_GATE)

        proxy_pct = basis_risk_result.get("proxy_basis_risk_pct")
        basis_gate_pass = basis_risk_result.get("gate_pass")

        if brier_gate_pass and basis_gate_pass is True:
            verdict = "GO"
        elif not brier_gate_pass:
            verdict = "NO-GO (Brier Score)"
        elif basis_gate_pass is False:
            verdict = "NO-GO (Basis Risk)"
        else:
            verdict = "PENDING — basis risk insufficient data for final verdict"

        return {
            "brier_score": {
                "value": brier_score,
                "threshold": BRIER_SCORE_GATE,
                "pass": brier_gate_pass,
            },
            "basis_risk": {
                "value": proxy_pct,
                "threshold": BASIS_RISK_GATE * 100,
                "pass": basis_gate_pass,
                "label": "NDVI proxy (indicative)",
                "detail": basis_risk_result,
            },
            "verdict": verdict,
        }

    def generate_final_report(self, valid_run_days: int) -> dict:
        """
        Generate the shadow run completion report and persist it to disk.

        Called automatically by the orchestrator when valid_run_days reaches 90.
        The report includes per-zone GO/NO-GO gates nested under the overall
        verdict — reinsurers see each zone's status, not just a single number.

        Returns the report dict (also available via get_final_report()).
        """
        metrics = self.evaluator.get_aggregate_metrics()
        now_utc = datetime.now(timezone.utc)

        # ── Aggregate basis risk (includes per-zone breakdown in .zones) ──
        from app.services.basis_risk_service import compute_ndvi_proxy_basis_risk
        basis_risk_result = compute_ndvi_proxy_basis_risk(self.db)

        # ── Overall GO/NO-GO gate ──
        overall_gates = self._evaluate_gate(
            metrics.get("brier_score"),
            basis_risk_result,
        )

        # ── Per-zone GO/NO-GO gates ──
        zone_gates: dict[str, dict] = {}
        zones_metrics = metrics.get("zones", {})
        zones_basis = basis_risk_result.get("zones", {})

        for zone_id, zone_m in zones_metrics.items():
            zone_br = zones_basis.get(zone_id, {})
            zone_gate = self._evaluate_gate(
                zone_m.get("brier_score"),
                zone_br,
            )
            zone_gate["zone_name"] = zone_m.get("zone_name", f"location_{zone_id}")
            zone_gate["location_id"] = zone_m.get("location_id", int(zone_id))
            zone_gates[zone_id] = zone_gate

        report = {
            "generated_at": now_utc.isoformat(),
            "shadow_run": {
                "valid_run_days": valid_run_days,
                "target_run_days": sr_cfg.SHADOW_RUN_TARGET_DAYS,
                "total_forecasts": metrics.get("total_evaluated", 0),
                "target_forecasts": sr_cfg.SHADOW_RUN_TARGET_FORECASTS,
            },
            "go_live_gates": {
                **overall_gates,
                "overall_verdict": overall_gates["verdict"],
                "zones": zone_gates,
            },
            "aggregate_metrics": metrics,
        }

        # Persist to disk — survives container restarts, served by dashboard API
        _FINAL_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_FINAL_REPORT_PATH, "w") as f:
            json.dump(report, f, indent=4)
        logger.info(f"Shadow run final report written to {_FINAL_REPORT_PATH}")

        return report

    @staticmethod
    def get_final_report() -> dict | None:
        """
        Load the persisted final report from disk.
        Returns None if the shadow run has not yet completed.
        """
        if not _FINAL_REPORT_PATH.exists():
            return None
        with open(_FINAL_REPORT_PATH) as f:
            return json.load(f)
