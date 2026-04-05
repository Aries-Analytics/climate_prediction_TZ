"""
MapSPAM 2020 — Kilombero Rice Yield Extractor
Source: Harvard Dataverse https://doi.org/10.7910/DVN/SWPENT

Downloads spam2020V2r0_global_yield.csv.zip (~71 MB, ~250 MB unzipped),
filters to Tanzania grid cells, then extracts Kilombero Basin cells and
saves processed output to data/external/ground_truth/mapspam_kilombero_rice.csv

MapSPAM yield units: kg/Ha — converted to MT/Ha on output.

Column naming convention:
  rice_a = all technologies combined
  rice_h = irrigated high input
  rice_i = high input rainfed
  rice_l = low input rainfed        ← primary for Kilombero smallholders
  rice_s = subsistence              ← secondary for Kilombero smallholders

Kilombero Basin bounding box (approximate):
  lat: -9.5 to -7.5
  lon: 35.5 to 37.5
"""

import io
import os
import sys
import zipfile
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
OUTPUT_FILE = OUTPUT_DIR / "mapspam_kilombero_rice.csv"
RAW_ZIP_FILE = RAW_DIR / "spam2020V2r0_global_yield.csv.zip"
RAW_CSV_FILE = RAW_DIR / "spam2020V2r0_global_yield_TZA.csv"  # Tanzania-filtered intermediate

DOWNLOAD_URL = "https://dataverse.harvard.edu/api/access/datafile/11596410"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HewaSense-GroundTruth/1.0; research)",
    "Accept": "*/*",
}

# Kilombero Basin bounding box
KILOMBERO_LAT_MIN = -9.5
KILOMBERO_LAT_MAX = -7.5
KILOMBERO_LON_MIN = 35.5
KILOMBERO_LON_MAX = 37.5

# Tanzania ISO
TZA_ISO3 = "TZA"


def download_mapspam(force: bool = False) -> Path:
    """Download MapSPAM yield ZIP if not already cached."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if RAW_ZIP_FILE.exists() and not force:
        print(f"[cache] ZIP already present: {RAW_ZIP_FILE} ({RAW_ZIP_FILE.stat().st_size / 1e6:.1f} MB)")
        return RAW_ZIP_FILE

    print("[download] Fetching MapSPAM yield CSV ZIP (~71 MB) — this may take a few minutes ...")

    # Step 1: Harvard Dataverse → 303 redirect to S3 signed URL
    # Do NOT follow redirects with original headers — S3 rejects carried auth/UA headers
    r1 = requests.get(DOWNLOAD_URL, headers=HEADERS, allow_redirects=False, timeout=30)
    if r1.status_code in (301, 302, 303, 307, 308):
        s3_url = r1.headers["Location"]
        print(f"  [redirect] Following to S3: {s3_url[:80]}...")
    elif r1.status_code == 200:
        s3_url = None
        r_final = r1
    else:
        r1.raise_for_status()

    # Step 2: Clean GET to S3 (no custom headers — S3 validates signature against exact headers)
    if s3_url:
        r_final = requests.get(s3_url, timeout=300, stream=True)
        r_final.raise_for_status()

    total = int(r_final.headers.get("Content-Length", 0))
    downloaded = 0
    chunks = []

    for chunk in r_final.iter_content(chunk_size=1024 * 512):  # 512 KB
        chunks.append(chunk)
        downloaded += len(chunk)
        if total:
            pct = downloaded / total * 100
            print(f"\r  {downloaded / 1e6:.1f} MB / {total / 1e6:.1f} MB ({pct:.0f}%)", end="", flush=True)

    print()
    raw_bytes = b"".join(chunks)

    with open(RAW_ZIP_FILE, "wb") as f:
        f.write(raw_bytes)

    print(f"[ok] Saved ZIP: {RAW_ZIP_FILE} ({len(raw_bytes) / 1e6:.1f} MB)")
    return RAW_ZIP_FILE


def extract_and_filter(zip_path: Path, force: bool = False) -> pd.DataFrame:
    """
    Open the ZIP, find the yield CSV(s), stream-filter to Tanzania + rice columns.
    Uses chunked reading to handle large global CSV without memory issues.
    """
    if RAW_CSV_FILE.exists() and not force:
        print(f"[cache] Tanzania intermediate file found: {RAW_CSV_FILE}")
        return pd.read_csv(RAW_CSV_FILE, low_memory=False)

    print(f"[extract] Opening ZIP: {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        all_names = zf.namelist()
        print(f"[info] Files in ZIP: {all_names}")

        # Find the yield CSV(s) — there may be multiple (one per technology)
        csv_files = [n for n in all_names if n.endswith(".csv")]
        print(f"[info] CSV files: {csv_files}")

        if not csv_files:
            raise ValueError(f"No CSV files found in ZIP. Contents: {all_names}")

        all_frames = []

        for csv_name in csv_files:
            print(f"[parse] Processing: {csv_name}")
            with zf.open(csv_name) as f:
                # Use chunked reading for large files
                chunks = []
                chunk_iter = pd.read_csv(
                    f,
                    chunksize=100_000,
                    low_memory=False,
                )
                for i, chunk in enumerate(chunk_iter):
                    # Normalise column names
                    chunk.columns = [c.strip().lower() for c in chunk.columns]

                    # Filter to Tanzania using iso3 or country column
                    iso_col = next((c for c in ["iso3", "iso_a3", "adm0_code"] if c in chunk.columns), None)
                    if iso_col:
                        chunk = chunk[chunk[iso_col].str.upper() == TZA_ISO3]
                    else:
                        # Filter by bounding box
                        lat_col = next((c for c in ["y", "lat", "latitude"] if c in chunk.columns), None)
                        lon_col = next((c for c in ["x", "lon", "longitude"] if c in chunk.columns), None)
                        if lat_col and lon_col:
                            chunk = chunk[
                                (chunk[lat_col] >= -12.0) & (chunk[lat_col] <= -1.0) &
                                (chunk[lon_col] >= 29.0) & (chunk[lon_col] <= 41.0)
                            ]

                    if not chunk.empty:
                        chunk = chunk.copy()
                        chunk["_source_file"] = csv_name
                        chunks.append(chunk)

                    if (i + 1) % 10 == 0:
                        print(f"  chunk {i + 1} processed ...")

                if chunks:
                    df_file = pd.concat(chunks, ignore_index=True)
                    print(f"  -> {len(df_file)} Tanzania rows from {csv_name}")
                    all_frames.append(df_file)
                else:
                    print(f"  -> 0 Tanzania rows from {csv_name}")

    if not all_frames:
        raise ValueError("No Tanzania rows found in MapSPAM ZIP")

    df_tz = pd.concat(all_frames, ignore_index=True)
    print(f"[info] Total Tanzania rows: {len(df_tz)}")
    print(f"[info] Columns: {list(df_tz.columns[:20])}")

    # Save Tanzania intermediate for faster re-runs
    df_tz.to_csv(RAW_CSV_FILE, index=False)
    print(f"[ok] Tanzania intermediate saved: {RAW_CSV_FILE}")

    return df_tz


def filter_kilombero_and_select_rice(df_tz: pd.DataFrame) -> pd.DataFrame:
    """
    Filter to Kilombero Basin bounding box and select rice yield columns.
    Converts yield from kg/Ha to MT/Ha.
    """
    lat_col = next((c for c in ["y", "lat", "latitude"] if c in df_tz.columns), None)
    lon_col = next((c for c in ["x", "lon", "longitude"] if c in df_tz.columns), None)

    if lat_col and lon_col:
        df_kilombero = df_tz[
            (df_tz[lat_col] >= KILOMBERO_LAT_MIN) & (df_tz[lat_col] <= KILOMBERO_LAT_MAX) &
            (df_tz[lon_col] >= KILOMBERO_LON_MIN) & (df_tz[lon_col] <= KILOMBERO_LON_MAX)
        ].copy()
        print(f"[info] Kilombero Basin cells: {len(df_kilombero)}")
    else:
        print("[warn] No lat/lon columns found — using all Tanzania rows")
        df_kilombero = df_tz.copy()

    # --- Select rice columns ---
    # MapSPAM column names: rice_a, rice_h, rice_i, rice_l, rice_s
    rice_cols = [c for c in df_kilombero.columns if c.startswith("rice_")]
    coord_cols = [c for c in [lat_col, lon_col, "iso3", "name_cntr", "alloc_key", "_source_file"]
                  if c and c in df_kilombero.columns]

    if not rice_cols:
        # The CSV might have tech-specific files (e.g. only rice_l in one file)
        # Try generic yield columns
        all_rice = [c for c in df_kilombero.columns if "rice" in c]
        print(f"[info] Rice-related columns: {all_rice}")
        rice_cols = all_rice

    if not rice_cols:
        print(f"[warn] No rice columns found. All columns: {list(df_kilombero.columns)}")
        return df_kilombero

    print(f"[info] Rice yield columns: {rice_cols}")

    # Select coordinate + rice columns
    keep_cols = list(dict.fromkeys(coord_cols + rice_cols))
    df_out = df_kilombero[keep_cols].copy()

    # Determine unit from the 'unit' column (MapSPAM 2020 uses 'mt/ha', older versions 'kg/ha')
    unit_val = ""
    if "unit" in df_out.columns:
        unit_vals = df_out["unit"].dropna().unique()
        unit_val = str(unit_vals[0]).lower() if len(unit_vals) > 0 else ""
        print(f"[info] Yield unit column value: '{unit_val}'")

    for col in rice_cols:
        numeric = pd.to_numeric(df_out[col], errors="coerce")
        if "kg" in unit_val:
            # kg/Ha → MT/Ha
            df_out[col + "_mt_ha"] = numeric / 1000.0
        else:
            # Already MT/Ha (MapSPAM 2020 uses mt/ha)
            df_out[col + "_mt_ha"] = numeric

    # Remove rows where all rice yields are zero or NaN (unfarmed cells)
    rice_mt_cols = [c + "_mt_ha" for c in rice_cols]
    has_rice = df_out[rice_mt_cols].sum(axis=1) > 0
    df_out = df_out[has_rice].copy()
    print(f"[info] Cells with non-zero rice production: {len(df_out)}")

    return df_out


def summarise(df: pd.DataFrame) -> None:
    if df.empty:
        print("[warn] Empty dataframe — no summary")
        return

    lat_col = next((c for c in ["y", "lat"] if c in df.columns), None)
    lon_col = next((c for c in ["x", "lon"] if c in df.columns), None)

    # Primary columns of interest
    rice_l = "rice_l_mt_ha"   # low input rainfed (most representative)
    rice_s = "rice_s_mt_ha"   # subsistence
    rice_a = "rice_a_mt_ha"   # all technologies

    print("\n" + "=" * 60)
    print("  MapSPAM 2020 — Kilombero Basin Rice Yield Summary")
    print("=" * 60)
    print(f"  Grid cells      : {len(df)}")

    if lat_col and lon_col:
        print(f"  Lat range       : {df[lat_col].min():.2f} to {df[lat_col].max():.2f}")
        print(f"  Lon range       : {df[lon_col].min():.2f} to {df[lon_col].max():.2f}")

    # MapSPAM 2020 uses rice_r (rainfed), rice_i (irrigated), rice_a (all tech)
    rice_r = "rice_r_mt_ha"
    for col, label in [(rice_r, "Rainfed (rice_r) - PRIMARY"),
                       (rice_l, "Low-input rainfed (rice_l)"),
                       (rice_s, "Subsistence (rice_s)"),
                       (rice_a, "All technologies (rice_a)")]:
        if col in df.columns:
            v = df[col].replace(0, float("nan")).dropna()
            if not v.empty:
                print(f"\n  {label}:")
                print(f"    mean={v.mean():.3f}  median={v.median():.3f}  "
                      f"min={v.min():.3f}  max={v.max():.3f}  n={len(v)}")

    print("=" * 60)
    print("\n  [note] Units: MT/Ha | Year: 2020 snapshot")
    print("  [note] Recommended primary: rice_l_mt_ha (low-input rainfed)")
    print("  [note] Kilombero smallholders are predominantly low-input rainfed")


def main(force: bool = False) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Download
    zip_path = download_mapspam(force=force)

    # 2. Extract and filter to Tanzania
    df_tz = extract_and_filter(zip_path, force=force)

    # 3. Filter to Kilombero + select rice
    df_kilombero = filter_kilombero_and_select_rice(df_tz)

    if df_kilombero.empty:
        print("[warn] No Kilombero rice cells — check bounding box or column names")

    # 4. Save
    df_kilombero.to_csv(OUTPUT_FILE, index=False)
    print(f"\n[ok] Processed data saved: {OUTPUT_FILE} ({len(df_kilombero)} rows)")

    # 5. Summarise
    summarise(df_kilombero)


if __name__ == "__main__":
    force_flag = "--force" in sys.argv
    main(force=force_flag)
