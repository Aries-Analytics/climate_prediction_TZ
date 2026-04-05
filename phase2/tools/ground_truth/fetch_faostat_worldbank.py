"""
FAOSTAT + World Bank — Tanzania Rice Yield Baseline
Fetches Tanzania national rice yield data from:
  1. FAOSTAT QCL API (rice-specific, item=27, element=5419=Yield Hg/Ha)
  2. World Bank API (cereal yield + rice production + rice area as proxy)

Both are free, unauthenticated public APIs.
Outputs: data/external/ground_truth/faostat_worldbank_tz_rice.csv

This serves as the programmatic replacement for HarvestStat Africa
(which is behind Cloudflare) and ILRI (which is restricted).
"""

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
OUTPUT_FILE = OUTPUT_DIR / "faostat_worldbank_tz_rice.csv"

# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
# FAOSTAT API — Tanzania(215), Rice paddy(27), Yield hg/Ha(5419)
FAOSTAT_RICE_YIELD_URL = (
    "https://fenixservices.fao.org/faostat/api/v1/en/data/QCL"
    "?area=215&item=27&element=5419&year=2000%3A2023&output_type=csv"
)
# World Bank — Tanzania cereal yield (kg/Ha)
WB_CEREAL_YIELD_URL = (
    "https://api.worldbank.org/v2/country/TZ/indicator/AG.YLD.CREL.KG"
    "?format=json&mrv=30&per_page=50"
)
# World Bank — Tanzania rice production (metric tons) — proxy to compute area + yield
WB_RICE_PROD_URL = (
    "https://api.worldbank.org/v2/country/TZ/indicator/AG.PRD.RICE.MT"
    "?format=json&mrv=35&per_page=50"
)
# World Bank — Tanzania permanent cropland area (Ha) — rough area proxy
WB_RICE_AREA_URL = (
    "https://api.worldbank.org/v2/country/TZ/indicator/AG.LND.CREL.HA"
    "?format=json&mrv=30&per_page=50"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0",
    "Accept": "application/json,text/csv,*/*",
}


# ---------------------------------------------------------------------------
# FAOSTAT
# ---------------------------------------------------------------------------
def fetch_faostat_rice() -> pd.DataFrame:
    """Fetch Tanzania rice paddy yield from FAOSTAT QCL API."""
    print("[faostat] Fetching Tanzania rice yield (item=27, Yield hg/Ha) ...")
    try:
        resp = requests.get(FAOSTAT_RICE_YIELD_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()

        # FAOSTAT returns CSV when output_type=csv
        from io import StringIO
        df = pd.read_csv(StringIO(resp.text))
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        print(f"[faostat] Received {len(df)} rows. Columns: {list(df.columns)}")

        # Find year and value columns
        year_col = next((c for c in df.columns if "year" in c), None)
        value_col = next((c for c in df.columns if "value" in c), None)

        if year_col and value_col:
            df_out = df[[year_col, value_col]].copy()
            df_out.columns = ["year", "yield_hg_ha"]
            df_out["yield_mt_ha"] = pd.to_numeric(df_out["yield_hg_ha"], errors="coerce") / 10000.0
            df_out["year"] = pd.to_numeric(df_out["year"], errors="coerce")
            df_out = df_out.dropna(subset=["year", "yield_mt_ha"])
            df_out["source"] = "FAOSTAT_QCL_rice"
            df_out["geography"] = "Tanzania (national)"
            df_out["crop"] = "rice_paddy"
            return df_out[["year", "yield_mt_ha", "source", "geography", "crop"]].sort_values("year")

        print(f"[faostat] Could not identify year/value columns in: {list(df.columns)}")
        return pd.DataFrame()

    except requests.exceptions.HTTPError as e:
        print(f"[faostat] HTTP error: {e} — server may be temporarily down")
        return pd.DataFrame()
    except Exception as e:
        print(f"[faostat] Failed: {e}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# World Bank
# ---------------------------------------------------------------------------
def _parse_wb_response(resp_json: list, value_label: str) -> pd.DataFrame:
    """Parse World Bank API JSON response into a clean DataFrame."""
    if len(resp_json) < 2 or not resp_json[1]:
        return pd.DataFrame()
    rows = []
    for item in resp_json[1]:
        year = item.get("date")
        value = item.get("value")
        if year and value is not None:
            rows.append({"year": int(year), value_label: float(value)})
    return pd.DataFrame(rows).sort_values("year")


def fetch_worldbank_cereal_yield() -> pd.DataFrame:
    """Fetch Tanzania cereal yield (kg/Ha) from World Bank."""
    print("[worldbank] Fetching Tanzania cereal yield (AG.YLD.CREL.KG) ...")
    try:
        resp = requests.get(WB_CEREAL_YIELD_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        df = _parse_wb_response(resp.json(), "cereal_yield_kg_ha")
        df["cereal_yield_mt_ha"] = df["cereal_yield_kg_ha"] / 1000.0
        print(f"[worldbank] Got {len(df)} rows (cereal yield)")
        return df
    except Exception as e:
        print(f"[worldbank] Cereal yield fetch failed: {e}")
        return pd.DataFrame()


def fetch_worldbank_rice_production() -> pd.DataFrame:
    """Fetch Tanzania rice production (MT) from World Bank."""
    print("[worldbank] Fetching Tanzania rice production (AG.PRD.RICE.MT) ...")
    try:
        resp = requests.get(WB_RICE_PROD_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        df = _parse_wb_response(resp.json(), "rice_production_mt")
        print(f"[worldbank] Got {len(df)} rows (rice production)")
        return df
    except Exception as e:
        print(f"[worldbank] Rice production fetch failed: {e}")
        return pd.DataFrame()


def fetch_worldbank_cereal_area() -> pd.DataFrame:
    """Fetch Tanzania cereal harvested area (Ha) — used as rice area proxy."""
    print("[worldbank] Fetching Tanzania cereal harvested area (AG.LND.CREL.HA) ...")
    try:
        resp = requests.get(WB_RICE_AREA_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        df = _parse_wb_response(resp.json(), "cereal_area_ha")
        print(f"[worldbank] Got {len(df)} rows (cereal area)")
        return df
    except Exception as e:
        print(f"[worldbank] Cereal area fetch failed: {e}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Combine World Bank into yield estimate
# ---------------------------------------------------------------------------
def build_worldbank_dataset() -> pd.DataFrame:
    """
    Build a Tanzania rice yield estimate from World Bank data.

    Strategy:
      - Use cereal yield as primary proxy (all cereals, roughly tracks rice)
      - Note: Tanzania cereal yield ~= rice yield in wet zones (Kilombero)
        because rice dominates in these areas
    """
    cereal_yield = fetch_worldbank_cereal_yield()
    rice_prod = fetch_worldbank_rice_production()

    rows = []

    if not cereal_yield.empty:
        for _, row in cereal_yield.iterrows():
            rows.append({
                "year": row["year"],
                "yield_mt_ha": round(row["cereal_yield_mt_ha"], 3),
                "source": "WorldBank_AG.YLD.CREL.KG",
                "geography": "Tanzania (national, all cereals)",
                "crop": "cereals_proxy",
                "note": "kg/Ha→MT/Ha: national cereal avg, not rice-specific",
            })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> pd.DataFrame:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    frames = []

    # Try FAOSTAT first (rice-specific)
    fao_df = fetch_faostat_rice()
    if not fao_df.empty:
        frames.append(fao_df)
        print(f"[ok] FAOSTAT: {len(fao_df)} rice yield records")
    else:
        print("[fallback] FAOSTAT unavailable — using World Bank cereal yield as proxy")

    # Always include World Bank (working baseline)
    wb_df = build_worldbank_dataset()
    if not wb_df.empty:
        frames.append(wb_df)
        print(f"[ok] World Bank: {len(wb_df)} cereal yield records")

    if not frames:
        print("[error] No data retrieved from any source")
        sys.exit(1)

    df_all = pd.concat(frames, ignore_index=True)
    df_all.to_csv(OUTPUT_FILE, index=False)
    print(f"\n[ok] Saved: {OUTPUT_FILE} ({len(df_all)} rows)")

    # Print summary
    print("\n" + "=" * 60)
    print("  FAOSTAT / World Bank — Tanzania Rice Yield Summary")
    print("=" * 60)

    for source, grp in df_all.groupby("source"):
        yields = grp["yield_mt_ha"].dropna()
        print(f"\n  Source  : {source}")
        print(f"  Rows    : {len(grp)}")
        print(f"  Period  : {int(grp['year'].min())} – {int(grp['year'].max())}")
        print(f"  Yield   : mean={yields.mean():.3f}  median={yields.median():.3f}  "
              f"min={yields.min():.3f}  max={yields.max():.3f} MT/Ha")

    print("=" * 60)
    print("\n  [note] FAOSTAT rice = national irrigated+rainfed average")
    print("  [note] WorldBank cereal = national all-cereal average")
    print("  [note] Both overestimate Kilombero rain-fed smallholder yields")
    print("  [note] Kilombero-specific range from literature: 1.2–1.8 MT/Ha")

    return df_all


if __name__ == "__main__":
    main()
