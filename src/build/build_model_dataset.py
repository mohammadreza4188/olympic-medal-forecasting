"""
build_model_dataset.py
======================
Merge panel v2 with discipline features, apply uniform transformations,
and write a model-ready dataset.

See references/phase5_research_protocol.md for the specification.
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

PANEL_V2 = PROCESSED / "panel_summer_macro_v2.csv"
DISC = PROCESSED / "discipline_features.csv"
OUT = PROCESSED / "model_dataset.csv"

NON_MAPPABLE_NOCS = {
    "URS","GDR","TCH","YUG","SCG","ANZ","BOH","EUN","ROC","IOA",
    "AIN","EOR","UAR","AHO","YMD","YAR","SAA","NBO","NFL","CRT","WIF",
}

DISC_COLS = [
    "rca_mean_weighted","rca_max","rca_p75",
    "n_sports_rca_gt1","n_sports_rca_gt1p5",
    "medal_hhi","n_sports_medal","medal_share_top_sport",
]

FILL_ZERO_COLS = DISC_COLS  # zero-fill is conceptually valid (see protocol)

LOG_COLS_PREFIX = ["gdp_const", "gdp_pcap_const", "population"]
LOG_COLS_SUFFIX = "_avg4y"


def pivot_block(disc, variant, window, suffix):
    sub = disc[(disc["variant"] == variant) & (disc["window"] == window)].copy()
    if len(sub) == 0:
        return pd.DataFrame(columns=["NOC", "Year"])
    keep = ["NOC", "Year"] + [c for c in DISC_COLS if c in sub.columns]
    sub = sub[keep].rename(columns={c: f"{c}_{suffix}" for c in DISC_COLS})
    return sub


def winsorize(df, cols, lower=None, upper=0.99):
    out = df.copy()
    for c in cols:
        if c not in out.columns:
            continue
        s = out[c].dropna()
        if len(s) < 10:
            continue
        hi = s.quantile(upper)
        lo = s.quantile(lower) if lower is not None else None
        if lo is not None:
            out[c] = out[c].clip(lower=lo, upper=hi)
        else:
            out[c] = out[c].clip(upper=hi)
    return out


def main():
    pkg = []
    pkg.append("=== Model dataset build ===")

    panel = pd.read_csv(PANEL_V2, encoding="utf-8-sig", low_memory=False)
    pkg.append(f"panel v2: shape={panel.shape} years={panel['Year'].min()}..{panel['Year'].max()} n_noc={panel['NOC'].nunique()}")

    disc = pd.read_csv(DISC, encoding="utf-8-sig", low_memory=False)
    pkg.append(f"discipline: shape={disc.shape} variants={sorted(disc['variant'].unique())} windows={sorted(disc['window'].unique())}")

    # Pivot discipline to wide per block
    d_base = pivot_block(disc, "total",  "last4", "base")
    d_cum  = pivot_block(disc, "total",  "cum",   "cum")
    d_fem  = pivot_block(disc, "female", "last4", "female")
    d_mal  = pivot_block(disc, "male",   "last4", "male")

    for name, blk, key in [
        ("D_base",   d_base, "base"),
        ("D_cum",    d_cum,  "cum"),
        ("D_female", d_fem,  "female"),
        ("D_male",   d_mal,  "male"),
    ]:
        if len(blk) > 1:
            pkg.append(f"  {name}: rows={len(blk)} cols={len(blk.columns)-2}")

    merged = panel.copy()
    for blk in [d_base, d_cum, d_fem, d_mal]:
        if len(blk) > 1:
            merged = merged.merge(blk, on=["NOC", "Year"], how="left")

    pkg.append(f"after merge: shape={merged.shape}")

    # has_discipline_data flag BEFORE fill
    base_cols = [f"{c}_base" for c in DISC_COLS if f"{c}_base" in merged.columns]
    if base_cols:
        merged["has_discipline_data"] = (
            merged[base_cols].notna().any(axis=1).astype(int)
        )
        pkg.append(f"  has_discipline_data mean = {merged['has_discipline_data'].mean():.3f}")

    # Zero-fill discipline (all blocks)
    for c in [col for col in merged.columns if any(col.endswith(f"_{s}") for s in ["base","cum","female","male"])]:
        merged[c] = merged[c].fillna(0)

    # Winsorize RCA-derived columns at 99pct
    rca_like = [
        c for c in merged.columns
        if c.startswith("rca_") or c.startswith("medal_hhi_") or c.startswith("medal_share_")
    ]
    merged = winsorize(merged, rca_like, upper=0.99)
    pkg.append(f"  winsorized {len(rca_like)} RCA-derived columns at 99pct")

    # Log transforms
    log_map = {}
    for base in LOG_COLS_PREFIX:
        src = f"{base}{LOG_COLS_SUFFIX}"
        if src in merged.columns:
            dst = f"log_{src}"
            merged[dst] = np.log1p(merged[src].clip(lower=0))
            log_map[src] = dst
    for c in ["mt_total", "mt_gold", "ae_total_medals", "ae_gold"]:
        if c in merged.columns:
            merged[f"log_{c}"] = np.log1p(merged[c].clip(lower=0))
    pkg.append(f"  log transform: {len(log_map)} WB columns + 4 medal columns")

    # Lag features
    merged = merged.sort_values(["NOC", "Year"]).reset_index(drop=True)
    for c in ["mt_total", "mt_gold"]:
        merged[f"lag_{c}"] = (
            merged.groupby("NOC")[c].shift(1).fillna(0).astype(int)
        )
    pkg.append("  lag features: lag_mt_total, lag_mt_gold")

    # Final filter: drop non-mappable NOCs (no macro features) and MIX
    before = len(merged)
    merged = merged[~merged["NOC"].isin(NON_MAPPABLE_NOCS)].copy()
    merged = merged[merged["NOC"] != "MIX"].copy()
    pkg.append(f"  dropped non-mappable NOCs + MIX: {before} -> {len(merged)}")

    # Sample boundaries
    prim = merged[(merged["Year"] >= 1996) & (merged["Year"] <= 2024)].copy()
    sec  = merged[(merged["Year"] >= 1960) & (merged["Year"] <= 2024)].copy()

    # Primary sample with complete macro features
    macro_required = [
        "log_gdp_const_avg4y", "log_gdp_pcap_const_avg4y",
        "log_population_avg4y", "lag_mt_total",
    ]
    prim_complete = prim.dropna(subset=macro_required).copy()
    sec_complete  = sec.dropna(subset=macro_required).copy()

    # Host feature (Summer Games host NOC per edition)
    HOST_MAP = {
        1960: "ITA", 1964: "JPN", 1968: "MEX", 1972: "FRG", 1976: "CAN",
        1980: "URS", 1984: "USA", 1988: "KOR", 1992: "ESP",
        1996: "USA", 2000: "AUS", 2004: "GRE", 2008: "CHN",
        2012: "GBR", 2016: "BRA", 2020: "JPN", 2024: "FRA",
    }
    merged["host"] = merged.apply(
        lambda r: int(r["NOC"] == HOST_MAP.get(int(r["Year"]), "")), axis=1
    )

    merged["sample_primary"]   = merged.index.isin(prim_complete.index).astype(int)
    merged["sample_secondary"] = merged.index.isin(sec_complete.index).astype(int)

    merged.to_csv(OUT, index=False, encoding="utf-8-sig")
    pkg.append(f"\nmodel_dataset.csv saved: shape={merged.shape}")

    pkg.append("\n--- sample sizes ---")
    pkg.append(f"  primary  (1996-2024, macro complete): rows={len(prim_complete):>5d}  editions={prim_complete['Year'].nunique()}  nocs={prim_complete['NOC'].nunique()}")
    pkg.append(f"  secondary(1960-2024, macro complete): rows={len(sec_complete):>5d}  editions={sec_complete['Year'].nunique()}  nocs={sec_complete['NOC'].nunique()}")

    pkg.append("\nprimary sample rows per edition:")
    tab = prim_complete.groupby("Year").size().rename("n_rows")
    pkg.append(tab.to_string())

    pkg.append("\nzero-medal share in primary:")
    pkg.append(f"  overall: {(prim_complete['mt_total']==0).mean():.3f}")
    for y in sorted(prim_complete["Year"].unique()):
        s = prim_complete[prim_complete["Year"] == y]
        if len(s):
            pkg.append(f"  {y}: zero_share={(s['mt_total']==0).mean():.3f}  n={len(s)}")

    pkg.append("\nfeature null rates (primary sample):")
    feat_cols = [
        "log_gdp_const_avg4y", "log_gdp_pcap_const_avg4y",
        "log_population_avg4y", "athletes", "sports", "events",
        "lag_mt_total", "lag_mt_gold", "female_share",
    ] + [c for c in merged.columns if c.startswith("rca_mean_weighted_")
         or c.startswith("medal_hhi_")]
    nulls = prim_complete[feat_cols].isna().mean().round(3)
    pkg.append(nulls[nulls > 0].to_string() if (nulls > 0).any() else "  none")

    pkg.append("\nsample rows (primary, 2024, top 5 by mt_total):")
    sample = prim_complete[prim_complete["Year"] == 2024].sort_values(
        "mt_total", ascending=False
    )[["NOC","mt_total","log_gdp_const_avg4y","log_population_avg4y",
       "athletes","lag_mt_total","rca_mean_weighted_base","medal_hhi_base"]].head(5)
    pkg.append(sample.to_string(index=False))

    report_path = REPORTS / "phase5_model_dataset.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Model dataset build report\n\n")
        f.write("Generated by `src/build/build_model_dataset.py`.\n")
        f.write("See `references/phase5_research_protocol.md` for specification.\n\n")
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
