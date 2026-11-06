"""
fetch_worldbank.py
==================
Fetch World Bank indicators (GDP, GDP per capita, population) and merge them
into the macro panel using the reference-year rule defined in
references/worldbank_protocol.md.

Usage (from project root):
    python src/worldbank/fetch_worldbank.py            # fetch or reuse cache, then merge
    python src/worldbank/fetch_worldbank.py --force    # force re-download

Requires:
    requests  (pip install requests)
"""

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

try:
    import requests
except ImportError:
    print("ERROR: requests library not installed. Run: pip install requests")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "worldbank"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
RAW_DIR.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

PANEL_IN = PROCESSED / "panel_summer_macro_v1.csv"
PANEL_OUT = PROCESSED / "panel_summer_macro_v2.csv"

INDICATORS = {
    "gdp_const":      "NY.GDP.MKTP.KD",
    "gdp_pcap_const": "NY.GDP.PCAP.KD",
    "population":     "SP.POP.TOTL",
}

DATE_START = 1956
DATE_END = 2025

# NOCs that cannot be mapped to World Bank series.
# These are kept in the panel with NaN economic features.
NON_MAPPABLE_NOCS = {
    "URS", "GDR", "TCH", "YUG", "SCG", "ANZ", "BOH",
    "EUN", "ROC", "IOA", "AIN", "EOR", "UAR", "AHO",
    "YMD", "YAR", "SAA", "NBO", "NFL", "CRT", "WIF",
}

# Explicit NOC -> ISO3 overrides. NOCs not listed here are assumed
# to use the same 3-letter code as ISO3.
NOC_ISO3_MAP = {
    "GER": "DEU", "NED": "NLD", "SUI": "CHE", "DEN": "DNK",
    "POR": "PRT", "GRE": "GRC", "INA": "IDN", "PHI": "PHL",
    "MAS": "MYS", "SIN": "SGP", "KSA": "SAU", "UAE": "ARE",
    "VIE": "VNM", "BUL": "BGR", "CRO": "HRV", "SLO": "SVN",
    "CRC": "CRI", "CHI": "CHL", "URU": "URY", "PAR": "PRY",
    "BIZ": "BLZ", "NCA": "NIC", "BAH": "BHS", "BAR": "BRB",
    "IVB": "VGB", "ISV": "VIR", "VIN": "VCT", "GRN": "GRD",
    "HAI": "HTI", "LBA": "LBY", "CGO": "COG", "CHA": "TCD",
    "GEQ": "GNQ", "GAM": "GMB", "GUI": "GIN", "GBS": "GNB",
    "LES": "LSO", "MAD": "MDG", "MAW": "MWI", "MTN": "MRT",
    "MRI": "MUS", "NIG": "NER", "NGR": "NGA", "SEY": "SYC",
    "RSA": "ZAF", "SUD": "SDN", "TAN": "TZA", "TOG": "TGO",
    "ZAM": "ZMB", "ZIM": "ZWE", "BAN": "BGD", "BHU": "BTN",
    "BRU": "BRN", "CAM": "KHM", "KUW": "KWT", "LIB": "LBN",
    "MGL": "MNG", "MYA": "MMR", "NEP": "NPL", "OMA": "OMN",
    "SRI": "LKA", "ALG": "DZA", "ANG": "AGO", "ARU": "ABW",
    "FRG": "DEU", "EUA": "DEU",
    # --- Added after Phase 3 coverage review ---
    "IRI": "IRN", "LAT": "LVA", "BOT": "BWA", "FIJ": "FJI",
    "HON": "HND", "ESA": "SLV", "GUA": "GTM", "BER": "BMU",
    "SAM": "WSM", "SKN": "KNA", "SOL": "SLB", "VAN": "VUT",
    "TGA": "TON", "PUR": "PRI", "BUR": "BFA", "CAY": "CYM",
    "ASA": "ASM", "MON": "MCO", "KOS": "XKX", "PLE": "PSE",
    "TPE": "TWN",
}


def noc_to_iso3(noc: str):
    if noc in NON_MAPPABLE_NOCS:
        return None
    return NOC_ISO3_MAP.get(noc, noc)


def wb_get_json(url, params, retries=3, backoff=3):
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, params=params, timeout=180)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == retries:
                raise
            print(f"  retry {attempt}/{retries} after error: {e}")
            time.sleep(backoff * attempt)


AGGREGATE_ISO3 = {
    "WLD", "HIC", "LIC", "LMC", "MIC", "UMC",
    "EAP", "ECA", "LCN", "MEA", "NAC", "SAS", "SSF",
    "ARB", "CEB", "EAR", "EAS", "ECS", "FCS",
    "LDC", "IDB", "IDX", "IDA", "IFB",
    "OED", "PRE", "PST", "TEA", "TEC", "TLA", "TMN", "TSA", "TSS",
}


def _clean_wb_df(df):
    """Drop WB aggregates (empty / region / income-group iso3) and dedupe (iso3, year)."""
    n_before = len(df)
    df = df.copy()
    df["iso3"] = df["iso3"].astype(str).str.strip()
    df = df[(df["iso3"] != "") & (df["iso3"] != "nan")]
    df = df[~df["iso3"].str.upper().isin(AGGREGATE_ISO3)]
    df = df.drop_duplicates(subset=["iso3", "year"], keep="first")
    print(f"  cleaned: {n_before} -> {len(df)} rows (aggregates/dupes removed)")
    return df


def fetch_indicator(alias, code, force=False):
    raw_path = RAW_DIR / f"{code}.csv"
    if raw_path.exists() and not force:
        print(f"  cache hit: {raw_path.name}")
        df = pd.read_csv(raw_path)
    else:
        print(f"  downloading {code} ...")
        url = f"https://api.worldbank.org/v2/country/all/indicator/{code}"
        params = {
            "date": f"{DATE_START}:{DATE_END}",
            "format": "json",
            "per_page": 20000,
        }
        data = wb_get_json(url, params)
        if not isinstance(data, list) or len(data) < 2:
            raise ValueError(f"unexpected World Bank response for {code}: {str(data)[:200]}")
        rows = []
        for r in data[1]:
            if r.get("value") is None:
                continue
            iso3 = r.get("countryiso3code") or ""
            if not iso3:
                continue
            rows.append({"iso3": iso3, "year": int(r["date"]), "value": float(r["value"])})
        df = pd.DataFrame(rows)
        df.to_csv(raw_path, index=False)
        print(f"  saved {len(df)} rows to {raw_path.name}")
    return _clean_wb_df(df)


def build_rolling_features(df_ind):
    """Return dataframe with *_avg4y and *_prev1y per (iso3, year)."""
    iso3s = df_ind["iso3"].unique().tolist()
    years = list(range(DATE_START, DATE_END + 1))
    grid = pd.MultiIndex.from_product([iso3s, years], names=["iso3", "year"]).to_frame(index=False)
    grid = grid.merge(df_ind, on=["iso3", "year"], how="left").sort_values(["iso3", "year"])

    def prior_avg(s):
        return s.shift(1).rolling(window=4, min_periods=2).mean()

    grid["avg4y"] = grid.groupby("iso3")["value"].transform(prior_avg)
    grid["prev1y"] = grid.groupby("iso3")["value"].transform(lambda s: s.shift(1))
    return grid[["iso3", "year", "avg4y", "prev1y"]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="force re-download of raw data")
    args = parser.parse_args()

    pkg = []
    pkg.append("=== World Bank fetch + merge ===")

    panel = pd.read_csv(PANEL_IN, encoding="utf-8-sig", low_memory=False)
    pkg.append(f"panel v1: shape={panel.shape} years={panel['Year'].min()}..{panel['Year'].max()} n_noc={panel['NOC'].nunique()}")

    # Map NOCs
    panel["iso3"] = panel["NOC"].map(noc_to_iso3)
    unmapped_nocs = sorted(panel.loc[panel["iso3"].isna(), "NOC"].unique().tolist())
    pkg.append(f"non-mappable NOCs (kept with NaN WB): {unmapped_nocs}")

    # Fetch indicators
    wb_frames = {}
    for alias, code in INDICATORS.items():
        pkg.append(f"\n--- {alias} ({code}) ---")
        df = fetch_indicator(alias, code, force=args.force)
        pkg.append(f"raw rows: {len(df)}  iso3s: {df['iso3'].nunique()}  years: {df['year'].min()}..{df['year'].max()}")
        feats = build_rolling_features(df)
        feats = feats.rename(columns={"avg4y": f"{alias}_avg4y", "prev1y": f"{alias}_prev1y"})
        wb_frames[alias] = feats

    # Verify coverage: which NOCs got zero WB rows?
    wb_iso3_set = set()
    for df in wb_frames.values():
        wb_iso3_set |= set(df["iso3"].unique())
    panel_iso3_set = set(panel["iso3"].dropna().unique())
    missing_iso3 = sorted(panel_iso3_set - wb_iso3_set)
    pkg.append(f"\nNOCs whose ISO3 has zero WB rows (to verify mapping): {missing_iso3}")

    # Merge each indicator
    merged = panel.copy()
    for alias, feats in wb_frames.items():
        merged = merged.merge(
            feats,
            left_on=["iso3", "Year"],
            right_on=["iso3", "year"],
            how="left",
        ).drop(columns=["year"])

    merged = merged.drop(columns=["iso3"])
    merged = merged.sort_values(["Year", "NOC"]).reset_index(drop=True)

    if len(merged) != len(panel):
        raise ValueError(
            "Merge expanded panel: %d -> %d rows. "
            "World Bank frame has duplicate (iso3, year) keys or NaN key matching."
            % (len(panel), len(merged))
        )

    merged.to_csv(PANEL_OUT, index=False, encoding="utf-8-sig")
    pkg.append(f"\npanel v2 saved: {PANEL_OUT}  shape={merged.shape}")

    # Missing rates
    new_cols = [
        "gdp_const_avg4y", "gdp_pcap_const_avg4y", "population_avg4y",
        "gdp_const_prev1y", "gdp_pcap_const_prev1y", "population_prev1y",
    ]
    pkg.append("\nmissing rate per new column (overall):")
    pkg.append(merged[new_cols].isna().mean().round(3).to_string())

    pkg.append("\ncoverage on key years (avg4y):")
    for y in [1960, 1980, 2000, 2008, 2016, 2020, 2024]:
        sub = merged[merged["Year"] == y]
        if len(sub) == 0:
            continue
        row = f"  {y}: n={len(sub):>3d}  gdp_cov={sub['gdp_const_avg4y'].notna().mean():.2f}"
        row += f"  pop_cov={sub['population_avg4y'].notna().mean():.2f}"
        pkg.append(row)

    pkg.append("\nsample rows (2024, top 5 by mt_total):")
    sample = (
        merged[merged["Year"] == 2024]
        .sort_values("mt_total", ascending=False)
        [["NOC", "mt_total", "gdp_const_avg4y", "gdp_pcap_const_avg4y", "population_avg4y"]]
        .head(5)
    )
    pkg.append(sample.to_string(index=False))

    # Full report
    report_path = REPORTS / "phase3_worldbank_merge.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# World Bank merge report\n\n")
        f.write("Generated by `src/worldbank/fetch_worldbank.py`.\n\n")
        f.write("```\n" + "\n".join(pkg) + "\n```\n")

    print("\n" + "=" * 60)
    print("PACKAGE_FOR_CHAT_BEGIN")
    print("=" * 60)
    for line in pkg:
        print(line)
    print("=" * 60)
    print("PACKAGE_FOR_CHAT_END")
    print("=" * 60)
    print(f"\nFull report: {report_path}")


if __name__ == "__main__":
    main()
