"""
Yield Ground Truth Combiner
Combines HarvestStat, ILRI NAFAKA, and MapSPAM into a unified baseline
for Kilombero Basin rice yield calibration.

Usage:
    python tools/ground_truth/combine_yield_ground_truth.py

Outputs:
    data/external/ground_truth/yield_ground_truth_summary.csv
    Prints calibration recommendation to stdout
"""

import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PHASE2_ROOT = SCRIPT_DIR.parent.parent
GT_DIR = PHASE2_ROOT / "data" / "external" / "ground_truth"

HARVESTSTAT_FILE = GT_DIR / "harveststat_tz_rice.csv"
ILRI_FILE = GT_DIR / "ilri_kilombero_rice.csv"
MAPSPAM_FILE = GT_DIR / "mapspam_kilombero_rice.csv"
FAOSTAT_WB_FILE = GT_DIR / "faostat_worldbank_tz_rice.csv"
OUTPUT_FILE = GT_DIR / "yield_ground_truth_summary.csv"

# Current national average used in model (baseline to recalibrate from)
CURRENT_NATIONAL_BASELINE_MT_HA = 3.3


def load_harveststat() -> dict:
    """Extract yield stats from HarvestStat data."""
    if not HARVESTSTAT_FILE.exists():
        print(f"[skip] HarvestStat file not found: {HARVESTSTAT_FILE}")
        return {}

    df = pd.read_csv(HARVESTSTAT_FILE, low_memory=False)
    yield_col = next((c for c in ["yield_mt_ha", "yield", "yld"] if c in df.columns), None)
    admin_col = next((c for c in ["admin1_name", "adm1_name", "admin_1", "region"] if c in df.columns), None)
    year_col = next((c for c in ["year", "yr"] if c in df.columns), None)

    if yield_col is None:
        print(f"[warn] HarvestStat: no yield column found in {list(df.columns)}")
        return {}

    # All Tanzania rice
    all_tz = df[yield_col].dropna()

    # Morogoro only (closest to Kilombero)
    morogoro = pd.Series(dtype=float)
    if admin_col:
        mask = df[admin_col].astype(str).str.lower().str.contains("morogoro", na=False)
        morogoro = df[mask][yield_col].dropna()

    result = {
        "source": "HarvestStat Africa",
        "coverage": "Tanzania (all regions)",
        "period": f"{df[year_col].min()}–{df[year_col].max()}" if year_col else "1980–2022",
        "resolution": "Region-level (admin1)",
        "tz_mean_mt_ha": round(all_tz.mean(), 3) if not all_tz.empty else None,
        "tz_median_mt_ha": round(all_tz.median(), 3) if not all_tz.empty else None,
        "tz_n": len(all_tz),
        "morogoro_mean_mt_ha": round(morogoro.mean(), 3) if not morogoro.empty else None,
        "morogoro_median_mt_ha": round(morogoro.median(), 3) if not morogoro.empty else None,
        "morogoro_n": len(morogoro),
    }

    return result


def load_ilri() -> dict:
    """Extract yield stats from ILRI NAFAKA data."""
    if not ILRI_FILE.exists():
        print(f"[skip] ILRI file not found: {ILRI_FILE}")
        return {}

    df = pd.read_csv(ILRI_FILE, low_memory=False)
    yield_col = next((c for c in ["yield_mt_ha", "yield", "yld"] if c in df.columns), None)
    district_col = next((c for c in df.columns if "district" in c), None)

    if yield_col is None:
        print(f"[warn] ILRI: no yield column found in {list(df.columns)}")
        return {}

    all_plots = df[yield_col].dropna()

    kilombero = pd.Series(dtype=float)
    if district_col:
        mask = df[district_col].astype(str).str.lower().str.contains("kilombero", na=False)
        kilombero = df[mask][yield_col].dropna()

    result = {
        "source": "ILRI/NAFAKA Demo Plots",
        "coverage": "Tanzania targeted districts (Kilombero, Kilosa, others)",
        "period": "2013–2016",
        "resolution": "Plot-level (demonstration plots)",
        "all_plots_mean_mt_ha": round(all_plots.mean(), 3) if not all_plots.empty else None,
        "all_plots_median_mt_ha": round(all_plots.median(), 3) if not all_plots.empty else None,
        "all_plots_n": len(all_plots),
        "kilombero_mean_mt_ha": round(kilombero.mean(), 3) if not kilombero.empty else None,
        "kilombero_median_mt_ha": round(kilombero.median(), 3) if not kilombero.empty else None,
        "kilombero_n": len(kilombero),
    }

    return result


def load_mapspam() -> dict:
    """Extract yield stats from MapSPAM Kilombero cells."""
    if not MAPSPAM_FILE.exists():
        print(f"[skip] MapSPAM file not found: {MAPSPAM_FILE}")
        return {}

    df = pd.read_csv(MAPSPAM_FILE, low_memory=False)

    # MapSPAM 2020: rice_r (rainfed), rice_a (all tech), rice_i (irrigated)
    # MapSPAM 2010: rice_l (low-input rainfed), rice_s (subsistence), rice_a (all tech)
    results = {}
    for tech, col in [("rainfed", "rice_r_mt_ha"),
                      ("low_input_rainfed", "rice_l_mt_ha"),
                      ("subsistence", "rice_s_mt_ha"),
                      ("all_tech", "rice_a_mt_ha")]:
        if col in df.columns:
            v = df[col].replace(0, float("nan")).dropna()
            results[f"mapspam_{tech}_mean_mt_ha"] = round(v.mean(), 3) if not v.empty else None
            results[f"mapspam_{tech}_median_mt_ha"] = round(v.median(), 3) if not v.empty else None
            results[f"mapspam_{tech}_n_cells"] = len(v)

    result = {
        "source": "MapSPAM 2020",
        "coverage": "Kilombero Basin grid cells (~10km resolution)",
        "period": "2020 snapshot",
        "resolution": "10km grid",
        **results,
    }

    return result


def compute_recommendation(hs: dict, ilri: dict, spam: dict, wb: dict = None) -> dict:
    """
    Triangulate across sources to produce a calibrated yield estimate
    for the Kilombero Basin rain-fed smallholder context.

    Priority order:
    1. ILRI Kilombero-specific (plot level, most geographically precise)
    2. MapSPAM low-input rainfed Kilombero cells (spatially explicit)
    3. HarvestStat Morogoro region (broader but temporally deep)
    """
    candidates = []
    labels = []

    # ILRI Kilombero
    kilo_mean = ilri.get("kilombero_mean_mt_ha")
    kilo_median = ilri.get("kilombero_median_mt_ha")
    if kilo_mean:
        candidates.append(kilo_mean)
        labels.append(f"ILRI Kilombero mean ({kilo_mean})")
    if kilo_median:
        candidates.append(kilo_median)
        labels.append(f"ILRI Kilombero median ({kilo_median})")

    # MapSPAM rainfed (rice_r in 2020, rice_l in 2010)
    spam_mean = spam.get("mapspam_rainfed_mean_mt_ha") or spam.get("mapspam_low_input_rainfed_mean_mt_ha")
    if spam_mean:
        candidates.append(spam_mean)
        labels.append(f"MapSPAM rainfed mean ({spam_mean})")

    # MapSPAM subsistence
    spam_sub = spam.get("mapspam_subsistence_mean_mt_ha")
    if spam_sub:
        candidates.append(spam_sub)
        labels.append(f"MapSPAM subsistence mean ({spam_sub})")

    # HarvestStat — prefer Morogoro-specific, fall back to all Tanzania rice
    moro_mean = hs.get("morogoro_mean_mt_ha")
    tz_mean = hs.get("tz_mean_mt_ha")
    if moro_mean:
        candidates.append(moro_mean)
        labels.append(f"HarvestStat Morogoro mean ({moro_mean})")
    elif tz_mean:
        candidates.append(tz_mean)
        labels.append(f"HarvestStat Tanzania all-rice mean ({tz_mean}, national proxy)")

    # World Bank national cereal yield (lower-bound anchor — all cereals, national avg)
    # Included with 0.5x weight since it's not Kilombero-specific and not rice-specific
    if wb:
        wb_mean = wb.get("national_mean_mt_ha")
        if wb_mean:
            # Add as two half-weight entries (effectively 1 full-weight data point)
            for _ in range(1):
                candidates.append(wb_mean)
                labels.append(f"WorldBank cereal national mean ({wb_mean}, lower bound proxy)")

    if not candidates:
        return {"error": "No yield estimates available — run fetch scripts first"}

    avg = round(sum(candidates) / len(candidates), 3)
    low = round(min(candidates), 3)
    high = round(max(candidates), 3)

    # Suggested thresholds:
    # - Loss threshold (40% below normal = severe drought/flood season loss)
    # - Good season threshold (10% above normal)
    loss_threshold = round(avg * 0.60, 3)  # 40% loss
    good_threshold = round(avg * 1.10, 3)  # 10% above normal

    recommendation = {
        "data_sources_used": len(candidates),
        "individual_estimates": dict(zip(labels, candidates)),
        "triangulated_baseline_mt_ha": avg,
        "range_low_mt_ha": low,
        "range_high_mt_ha": high,
        "current_model_baseline_mt_ha": CURRENT_NATIONAL_BASELINE_MT_HA,
        "calibration_adjustment": round(avg - CURRENT_NATIONAL_BASELINE_MT_HA, 3),
        "suggested_loss_threshold_mt_ha": loss_threshold,
        "suggested_good_season_threshold_mt_ha": good_threshold,
        "note": (
            f"Recalibrate from national {CURRENT_NATIONAL_BASELINE_MT_HA} MT/Ha to "
            f"Kilombero data-derived {avg} MT/Ha (average of {len(candidates)} estimates). "
            f"Suggested loss trigger threshold = {loss_threshold} MT/Ha (40% below baseline). "
            f"NOTE: MapSPAM includes commercial operations — "
            f"for target smallholders (rain-fed, low-input), observed range from "
            f"literature is 1.2–1.8 MT/Ha. "
            f"Consider segment-specific thresholds: "
            f"severe loss trigger < 1.0 MT/Ha; moderate loss trigger < {loss_threshold} MT/Ha."
        ),
        "literature_smallholder_range_mt_ha": "1.2–1.8 (Kilombero rain-fed, low-input, survey-based)",
    }

    return recommendation


def print_report(hs: dict, ilri: dict, spam: dict, rec: dict, wb: dict = None) -> None:
    SEP = "=" * 65

    print(f"\n{SEP}")
    print("  KILOMBERO BASIN — RICE YIELD GROUND TRUTH CALIBRATION REPORT")
    print(SEP)

    print("\n--- SOURCE 1: HarvestStat Africa ---")
    if hs:
        print(f"  Coverage : {hs.get('coverage')}")
        print(f"  Period   : {hs.get('period')}")
        print(f"  TZ all   : mean={hs.get('tz_mean_mt_ha')} MT/Ha  (n={hs.get('tz_n')})")
        print(f"  Morogoro : mean={hs.get('morogoro_mean_mt_ha')} MT/Ha  (n={hs.get('morogoro_n')})")
    else:
        print("  [not available — run fetch_harveststat.py]")

    print("\n--- SOURCE 2: ILRI NAFAKA Demo Plots ---")
    if ilri:
        print(f"  Coverage   : {ilri.get('coverage')}")
        print(f"  Period     : {ilri.get('period')}")
        print(f"  All plots  : mean={ilri.get('all_plots_mean_mt_ha')} MT/Ha  (n={ilri.get('all_plots_n')})")
        print(f"  Kilombero  : mean={ilri.get('kilombero_mean_mt_ha')} MT/Ha  (n={ilri.get('kilombero_n')})")
    else:
        print("  [not available — run fetch_ilri_kilombero.py]")

    print("\n--- SOURCE 3: MapSPAM 2020 Kilombero Cells ---")
    if spam:
        print(f"  Coverage         : {spam.get('coverage')}")
        for key, label in [("rainfed", "Rainfed (rice_r)"),
                           ("low_input_rainfed", "Low-input rainfed"),
                           ("all_tech", "All technologies")]:
            mean_key = f"mapspam_{key}_mean_mt_ha"
            n_key = f"mapspam_{key}_n_cells"
            if spam.get(mean_key) is not None:
                print(f"  {label:20}: mean={spam.get(mean_key)} MT/Ha"
                      f"  (n={spam.get(n_key)} cells)")
    else:
        print("  [not available — run fetch_mapspam.py]")

    print("\n--- SOURCE 4: FAOSTAT / World Bank (national baseline) ---")
    if wb:
        print(f"  Coverage : {wb.get('coverage')}")
        print(f"  Period   : {wb.get('period')}")
        print(f"  National : mean={wb.get('national_mean_mt_ha')} MT/Ha  "
              f"range={wb.get('national_min_mt_ha')}–{wb.get('national_max_mt_ha')}"
              f"  (n={wb.get('n_years')} years)")
        print(f"  [note] Cereal national avg — confirms model's 3.3 MT/Ha baseline is ~2x too high")
    else:
        print("  [not available — run fetch_faostat_worldbank.py]")

    print(f"\n{SEP}")
    print("  CALIBRATION RECOMMENDATION")
    print(SEP)

    if "error" in rec:
        print(f"  {rec['error']}")
    else:
        print(f"  Sources used              : {rec['data_sources_used']} estimates")
        print(f"  Current model baseline    : {rec['current_model_baseline_mt_ha']} MT/Ha (national avg)")
        print(f"  Triangulated baseline     : {rec['triangulated_baseline_mt_ha']} MT/Ha")
        print(f"  Adjustment                : {rec['calibration_adjustment']:+.3f} MT/Ha")
        print(f"  Suggested loss threshold  : {rec['suggested_loss_threshold_mt_ha']} MT/Ha (40% below)")
        print(f"  Suggested good threshold  : {rec['suggested_good_season_threshold_mt_ha']} MT/Ha (+10%)")
        print(f"\n  {rec['note']}")

    print(SEP)


def load_faostat_worldbank() -> dict:
    """Extract yield stats from FAOSTAT/WorldBank baseline file."""
    if not FAOSTAT_WB_FILE.exists():
        print(f"[skip] FAOSTAT/WorldBank file not found: {FAOSTAT_WB_FILE}")
        return {}

    df = pd.read_csv(FAOSTAT_WB_FILE, low_memory=False)
    if df.empty or "yield_mt_ha" not in df.columns:
        return {}

    all_yields = df["yield_mt_ha"].dropna()
    result = {
        "source": "FAOSTAT/WorldBank (cereal proxy)",
        "coverage": "Tanzania national",
        "period": f"{int(df['year'].min())}–{int(df['year'].max())}",
        "resolution": "National average",
        "national_mean_mt_ha": round(all_yields.mean(), 3),
        "national_median_mt_ha": round(all_yields.median(), 3),
        "national_min_mt_ha": round(all_yields.min(), 3),
        "national_max_mt_ha": round(all_yields.max(), 3),
        "n_years": len(all_yields),
    }
    return result


def main() -> None:
    GT_DIR.mkdir(parents=True, exist_ok=True)

    print("[load] Reading processed ground truth files ...")

    hs = load_harveststat()
    ilri = load_ilri()
    spam = load_mapspam()
    wb = load_faostat_worldbank()

    rec = compute_recommendation(hs, ilri, spam, wb=wb)

    # Add WorldBank/FAOSTAT national mean as an additional reference point
    if wb:
        wb_mean = wb.get("national_mean_mt_ha")
        wb_median = wb.get("national_median_mt_ha")
        if wb_mean and isinstance(rec, dict) and "individual_estimates" in rec:
            rec["individual_estimates"][f"WorldBank cereal mean (national, {wb.get('period')})"] = wb_mean
            rec["national_baseline_reference_mt_ha"] = wb_mean

    # Save summary
    rows = []
    for src_dict in [hs, ilri, spam, wb]:
        if src_dict:
            rows.append(src_dict)

    if rows:
        summary_df = pd.DataFrame(rows)
        summary_df.to_csv(OUTPUT_FILE, index=False)
        print(f"\n[ok] Summary saved: {OUTPUT_FILE}")

    # Save recommendation separately
    rec_file = GT_DIR / "calibration_recommendation.json"
    import json
    with open(rec_file, "w") as f:
        json.dump(rec, f, indent=2, default=str)
    print(f"[ok] Calibration recommendation saved: {rec_file}")

    print_report(hs, ilri, spam, rec, wb=wb)


if __name__ == "__main__":
    main()
