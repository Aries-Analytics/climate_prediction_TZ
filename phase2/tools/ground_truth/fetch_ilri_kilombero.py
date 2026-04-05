"""
ILRI / NAFAKA Kilombero Rice Yield Downloader
Source: Harvard Dataverse https://doi.org/10.7910/DVN/V4HO79

Downloads yield-data-ar-nafaka-project.xls (~78 KB), extracts rice yield data
from demonstration plots in Kilombero and other targeted districts in Tanzania,
and saves processed output to data/external/ground_truth/ilri_kilombero_rice.csv

This dataset covers AR-NAFAKA project demonstration plots (~2013–2016)
and is used to ground-truth the yield threshold for Kilombero Basin.
"""

import os
import sys
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PHASE2_ROOT = SCRIPT_DIR.parent.parent
OUTPUT_DIR = PHASE2_ROOT / "data" / "external" / "ground_truth"
RAW_DIR = PHASE2_ROOT / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "ilri_kilombero_rice.csv"
RAW_FILE = RAW_DIR / "ilri_nafaka_yield.xls"

DOWNLOAD_URL = "https://dataverse.harvard.edu/api/access/datafile/3040660"

# API token — set HARVARD_DV_TOKEN env var or pass --token=<value> on command line
API_TOKEN = os.environ.get("HARVARD_DV_TOKEN", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HewaSense-GroundTruth/1.0; research)",
    "Accept": "application/vnd.ms-excel,*/*",
}


def download_ilri(force: bool = False) -> Path:
    """Download the ILRI NAFAKA yield XLS if not already cached."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if RAW_FILE.exists() and not force:
        print(f"[cache] Raw file already present: {RAW_FILE} ({RAW_FILE.stat().st_size / 1024:.1f} KB)")
        return RAW_FILE

    print("[download] Fetching ILRI NAFAKA yield XLS (~78 KB) ...")

    if not API_TOKEN:
        print("[error] No API token found. Set HARVARD_DV_TOKEN env var or pass --token=<value>")
        sys.exit(1)

    # Step 1: Harvard Dataverse → 303 redirect to S3 signed URL
    # X-Dataverse-key authenticates the request; stripped before following to S3
    auth_headers = {**HEADERS, "X-Dataverse-key": API_TOKEN}
    r1 = requests.get(DOWNLOAD_URL, headers=auth_headers, allow_redirects=False, timeout=30)
    if r1.status_code in (301, 302, 303, 307, 308):
        s3_url = r1.headers["Location"]
        print(f"  [redirect] Following to S3: {s3_url[:80]}...")
        # Step 2: Clean GET to S3 (no custom headers)
        resp = requests.get(s3_url, timeout=60)
    elif r1.status_code == 200:
        resp = r1
    else:
        r1.raise_for_status()

    resp.raise_for_status()

    with open(RAW_FILE, "wb") as f:
        f.write(resp.content)

    print(f"[ok] Saved raw file: {RAW_FILE} ({len(resp.content) / 1024:.1f} KB)")
    return RAW_FILE


def process_ilri(raw_path: Path) -> pd.DataFrame:
    """
    Parse all sheets in the NAFAKA yield XLS and extract rice yield data.

    The dataset covers demonstration plots across multiple Tanzania districts
    including Kilombero, Kilosa, and others. Units expected: MT/Ha or kg/Ha.
    """
    print(f"[parse] Reading {raw_path} ...")

    # Read all sheets
    try:
        xls = pd.ExcelFile(raw_path, engine="xlrd")
    except Exception:
        # Try openpyxl for newer formats
        xls = pd.ExcelFile(raw_path, engine="openpyxl")

    print(f"[info] Sheets found: {xls.sheet_names}")

    all_frames = []
    for sheet in xls.sheet_names:
        try:
            df_sheet = pd.read_excel(raw_path, sheet_name=sheet)
            df_sheet.columns = [str(c).strip().lower().replace(" ", "_") for c in df_sheet.columns]
            df_sheet["_sheet"] = sheet
            all_frames.append(df_sheet)
            print(f"  Sheet '{sheet}': {df_sheet.shape} — cols: {list(df_sheet.columns[:10])}")
        except Exception as e:
            print(f"  [warn] Could not read sheet '{sheet}': {e}")

    if not all_frames:
        raise ValueError("No sheets could be read from the XLS file")

    # Combine all sheets
    df = pd.concat(all_frames, ignore_index=True, sort=False)
    print(f"[info] Combined shape: {df.shape}")
    print(f"[info] All columns: {list(df.columns)}")

    # --- Identify yield column ---
    yield_col = None
    yield_candidates = ["yield", "yld", "yield_(mt/ha)", "yield_mt/ha", "yield_mt_ha",
                        "grain_yield", "rice_yield", "paddy_yield", "yield_(t/ha)", "yield_t_ha"]
    for cand in yield_candidates:
        if cand in df.columns:
            yield_col = cand
            break
    # Fuzzy search
    if yield_col is None:
        for col in df.columns:
            if "yield" in col or "yld" in col:
                yield_col = col
                break

    if yield_col:
        print(f"[info] Yield column identified: '{yield_col}'")
        # Coerce to numeric
        df[yield_col] = pd.to_numeric(df[yield_col], errors="coerce")

        # Detect unit: if mean > 20, likely kg/Ha → convert
        valid = df[yield_col].dropna()
        if not valid.empty and valid.mean() > 20:
            print(f"[info] Yield mean={valid.mean():.1f} — assuming kg/Ha, converting to MT/Ha")
            df["yield_mt_ha"] = df[yield_col] / 1000.0
        else:
            df["yield_mt_ha"] = df[yield_col]
    else:
        print(f"[warn] Could not identify a yield column. Numeric columns: "
              f"{[c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]}")

    # --- Filter to rice rows if crop column exists ---
    crop_col = next((c for c in df.columns if "crop" in c or "product" in c), None)
    if crop_col:
        rice_mask = df[crop_col].astype(str).str.lower().str.contains("rice|paddy", na=False)
        df_rice = df[rice_mask].copy()
        print(f"[info] Rice rows after crop filter: {len(df_rice)}")
    else:
        print("[info] No crop column — keeping all rows (dataset is likely rice-only)")
        df_rice = df.copy()

    # --- Standardise output columns ---
    district_col = next((c for c in df_rice.columns if "district" in c), None)
    season_col = next((c for c in df_rice.columns if "season" in c or "year" in c or "yr" in c), None)

    output_cols = []
    for c in [district_col, season_col, crop_col, "yield_mt_ha", "_sheet"]:
        if c and c in df_rice.columns:
            output_cols.append(c)
    # Add remaining numeric columns
    for c in df_rice.columns:
        if c not in output_cols and pd.api.types.is_numeric_dtype(df_rice[c]):
            output_cols.append(c)

    df_out = df_rice[list(dict.fromkeys(output_cols))].copy()  # deduplicate while preserving order

    return df_out


def summarise(df: pd.DataFrame) -> None:
    if df.empty:
        print("[warn] Empty dataframe — no summary")
        return

    yield_col = next((c for c in ["yield_mt_ha", "yield", "yld"] if c in df.columns), None)
    district_col = next((c for c in df.columns if "district" in c), None)

    print("\n" + "=" * 60)
    print("  ILRI NAFAKA — Tanzania Demo Plot Rice Yield Summary")
    print("=" * 60)
    print(f"  Total rows      : {len(df)}")

    if district_col:
        print(f"  Districts       : {df[district_col].nunique()} — "
              f"{', '.join(str(v) for v in df[district_col].dropna().unique()[:10])}")

    if yield_col:
        valid = df[yield_col].dropna()
        print(f"  Yield MT/Ha     : mean={valid.mean():.3f}  median={valid.median():.3f}  "
              f"min={valid.min():.3f}  max={valid.max():.3f}  n={len(valid)}")

        if district_col:
            kilombero = df[df[district_col].astype(str).str.lower().str.contains("kilombero", na=False)]
            if not kilombero.empty:
                kv = kilombero[yield_col].dropna()
                print(f"\n  Kilombero only  : n={len(kv)}  mean={kv.mean():.3f}  "
                      f"median={kv.median():.3f}  min={kv.min():.3f}  max={kv.max():.3f}")
            else:
                print("  [info] No 'Kilombero' district rows found")

    print("=" * 60)


def main(force: bool = False) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Download
    raw_path = download_ilri(force=force)

    # 2. Process
    df = process_ilri(raw_path)

    if df.empty:
        print("[warn] Processing yielded empty dataframe")

    # 3. Save
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n[ok] Processed data saved: {OUTPUT_FILE} ({len(df)} rows)")

    # 4. Summarise
    summarise(df)


if __name__ == "__main__":
    force_flag = "--force" in sys.argv
    # Allow --token=<value> as CLI alternative to env var
    for arg in sys.argv[1:]:
        if arg.startswith("--token="):
            API_TOKEN = arg.split("=", 1)[1]
            break
    main(force=force_flag)
