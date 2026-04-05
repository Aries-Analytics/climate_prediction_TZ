"""
HarvestStat Africa — Rice Yield Downloader
Source: Dryad https://datadryad.org/dataset/doi:10.5061/dryad.vq83bk42w

Downloads hvstat_africa_data_v1.0.csv (23 MB), filters to Tanzania + rice,
and saves processed output to data/external/ground_truth/harveststat_tz_rice.csv
"""

import io
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
OUTPUT_FILE = OUTPUT_DIR / "harveststat_tz_rice.csv"
RAW_FILE = RAW_DIR / "hvstat_africa_data_v1.0.csv"

DATASET_PAGE_URL = "https://datadryad.org/dataset/doi:10.5061/dryad.vq83bk42w"
DOWNLOAD_URL = "https://datadryad.org/downloads/file_stream/4028550"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def download_harveststat(force: bool = False) -> Path:
    """Download the raw HarvestStat CSV if not already cached."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if RAW_FILE.exists() and not force:
        print(f"[cache] Raw file already present: {RAW_FILE} ({RAW_FILE.stat().st_size / 1e6:.1f} MB)")
        return RAW_FILE

    print(f"[download] Fetching HarvestStat Africa CSV (~23 MB) ...")

    # Dryad requires a session — visit dataset page first to obtain cookies
    session = requests.Session()
    session.headers.update(HEADERS)
    print("  [session] Visiting dataset page to obtain session cookies ...")
    try:
        session.get(DATASET_PAGE_URL, timeout=30)
    except Exception as e:
        print(f"  [warn] Dataset page visit failed (proceeding anyway): {e}")

    resp = session.get(
        DOWNLOAD_URL,
        headers={"Referer": DATASET_PAGE_URL, "Accept": "text/csv,application/csv,*/*"},
        timeout=120,
        stream=True,
        allow_redirects=True,
    )
    resp.raise_for_status()

    total = int(resp.headers.get("Content-Length", 0))
    downloaded = 0
    chunks = []

    for chunk in resp.iter_content(chunk_size=1024 * 256):  # 256 KB chunks
        chunks.append(chunk)
        downloaded += len(chunk)
        if total:
            pct = downloaded / total * 100
            print(f"\r  {downloaded / 1e6:.1f} MB / {total / 1e6:.1f} MB ({pct:.0f}%)", end="", flush=True)

    print()
    raw_bytes = b"".join(chunks)

    with open(RAW_FILE, "wb") as f:
        f.write(raw_bytes)

    print(f"[ok] Saved raw file: {RAW_FILE} ({len(raw_bytes) / 1e6:.1f} MB)")
    return RAW_FILE


def process_harveststat(raw_path: Path) -> pd.DataFrame:
    """
    Filter raw HarvestStat CSV to Tanzania + rice only.

    Expected columns (from the dataset README):
      country_iso, country_name, admin1_name, admin2_name, crop, product,
      year, harvested_area_ha, production_mt, yield_mt_ha, source, ...
    """
    print(f"[parse] Reading {raw_path} ...")
    df = pd.read_csv(raw_path, low_memory=False)

    print(f"[info] Raw shape: {df.shape}")
    print(f"[info] Columns: {list(df.columns)}")

    # --- Normalise column names to lowercase ---
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # --- Identify country column ---
    country_col = None
    for cand in ["country_iso", "iso3", "country_code", "adm0_iso", "iso_a3"]:
        if cand in df.columns:
            country_col = cand
            break
    if country_col is None:
        # Fall back to name-based filter
        for cand in ["country_name", "country", "adm0_name"]:
            if cand in df.columns:
                country_col = cand
                break

    if country_col is None:
        raise ValueError(f"Cannot identify country column. Available: {list(df.columns)}")

    print(f"[info] Using country column: '{country_col}'")

    # --- Filter Tanzania ---
    tz_mask = (
        df[country_col].str.upper().isin(["TZ", "TZA", "TANZANIA", "UNITED REPUBLIC OF TANZANIA"])
        | df[country_col].str.lower().str.contains("tanzania", na=False)
    )
    df_tz = df[tz_mask].copy()
    print(f"[info] Tanzania rows: {len(df_tz)}")

    if df_tz.empty:
        print("[warn] No Tanzania rows found — check the country column values:")
        print(df[country_col].value_counts().head(20))
        return df_tz

    # --- Filter rice ---
    crop_col = None
    for cand in ["crop", "crop_name", "commodity", "product"]:
        if cand in df_tz.columns:
            crop_col = cand
            break

    if crop_col:
        rice_mask = df_tz[crop_col].str.lower().str.contains("rice", na=False)
        df_rice = df_tz[rice_mask].copy()
        print(f"[info] Tanzania + rice rows: {len(df_rice)}")
    else:
        print("[warn] No crop column found — keeping all Tanzania rows")
        df_rice = df_tz

    # --- Identify yield column ---
    yield_col = None
    for cand in ["yield_mt_ha", "yield", "yld", "yield_hg_ha", "yld_mt_ha"]:
        if cand in df_rice.columns:
            yield_col = cand
            break

    if yield_col:
        # Convert hg/Ha → MT/Ha if needed (FAO uses hg/Ha in some datasets: 1 MT/Ha = 10,000 hg/Ha)
        if "hg" in yield_col:
            df_rice = df_rice.copy()
            df_rice["yield_mt_ha"] = df_rice[yield_col] / 10000.0
            yield_col = "yield_mt_ha"
            print("[info] Converted yield from hg/Ha to MT/Ha")
        print(f"[info] Yield column: '{yield_col}'")

    return df_rice


def summarise(df: pd.DataFrame) -> None:
    """Print a summary of the processed dataset."""
    if df.empty:
        print("[warn] Empty dataframe — no summary to show")
        return

    # Identify year and yield columns
    year_col = next((c for c in ["year", "yr"] if c in df.columns), None)
    yield_col = next((c for c in ["yield_mt_ha", "yield", "yld", "yield_hg_ha"] if c in df.columns), None)
    admin_col = next((c for c in ["admin1_name", "adm1_name", "region", "province"] if c in df.columns), None)

    print("\n" + "=" * 60)
    print("  HarvestStat Africa — Tanzania Rice Summary")
    print("=" * 60)
    print(f"  Total rows      : {len(df)}")

    if year_col:
        print(f"  Year range      : {df[year_col].min()} – {df[year_col].max()}")
    if admin_col:
        print(f"  Admin units     : {df[admin_col].nunique()} ({', '.join(str(v) for v in sorted(df[admin_col].dropna().unique())[:8])})")
    if yield_col:
        valid = df[yield_col].dropna()
        print(f"  Yield MT/Ha     : mean={valid.mean():.3f}  median={valid.median():.3f}  "
              f"min={valid.min():.3f}  max={valid.max():.3f}")

        # Morogoro-specific if present
        if admin_col:
            moro = df[df[admin_col].str.lower().str.contains("morogoro", na=False)]
            if not moro.empty:
                mv = moro[yield_col].dropna()
                print(f"\n  Morogoro only   : n={len(mv)}  mean={mv.mean():.3f}  "
                      f"median={mv.median():.3f}  min={mv.min():.3f}  max={mv.max():.3f}")
            else:
                print("  [info] No 'Morogoro' rows in admin column")

    print("=" * 60)


def main(force: bool = False) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Download
    raw_path = download_harveststat(force=force)

    # 2. Process
    df = process_harveststat(raw_path)

    if df.empty:
        print("[error] Processing yielded empty dataframe — check column names above")
        sys.exit(1)

    # 3. Save
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n[ok] Processed data saved: {OUTPUT_FILE} ({len(df)} rows)")

    # 4. Summarise
    summarise(df)


if __name__ == "__main__":
    force_flag = "--force" in sys.argv
    main(force=force_flag)
