"""
build_per_sport_dataset.py
==========================
Build the per-sport dataset for Chapter 3.5 (Ch4 of dissertation).

Output: data/processed/per_sport_dataset.csv
Keys: NOC, Year, Sport
Target: medals_in_sport
See references/ch05_persport_protocol.md for the full specification.

Run: python src/build/build_per_sport_dataset.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

AE_PATH = RAW / "athlete_events_through_2026.csv"
MACRO_DS = PROCESSED / "model_dataset_team.csv"
DISC_SPORT = PROCESSED / "discipline_sport_medals.csv"
OUT = PROCESSED / "per_sport_dataset.csv"

PRIMARY_YEARS = [1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024]
MIN_SPORT_EDITIONS = 5

MACRO_FEATURES = [
    "log_gdp_const_avg4y", "log_gdp_pcap_const_avg4y", "log_population_avg4y",
    "athletes", "sports", "events", "female_share", "host",
    "lag_mt_total", "lag_mt_gold",
]


def build_medal_grid(ae):
    """(NOC, Year, Sport) -> medals_in_sport, using team de-dup."""
    sub = ae[(ae["Season"] == "Summer") & (ae["Medal"].notna())].copy()
    sub = sub[sub["Year"].isin(PRIMARY_YEARS)]
    sub = sub.drop_duplicates(subset=["NOC", "Year", "Sport", "Event", "Medal"])
    g = sub.groupby(["NOC", "Year", "Sport"]).size().rename("medals_in_sport").reset_index()
    return g


def build_participation_grid(ae):
    """(NOC, Year, Sport) -> n_athletes_in_sport."""
    sub = ae[(ae["Season"] == "Summer")].copy()
    sub = sub[sub["Year"].isin(PRIMARY_YEARS)]
    g = (
        sub.groupby(["NOC", "Year", "Sport"])["ID"]
        .nunique()
        .rename("n_athletes_in_sport")
        .reset_index()
    )
    return g


def build_sport_level(ae):
    """(Year, Sport) -> sport_n_events (pre-Games, scheduled)."""
    sub = ae[(ae["Season"] == "Summer")].copy()
    sub = sub[sub["Year"].isin(PRIMARY_YEARS)]
    g = (
        sub.groupby(["Year", "Sport"])["Event"]
        .nunique()
        .rename("sport_n_events")
        .reset_index()
    )
    return g


def main():
    pkg = ["=== Chapter 3.5: per-sport dataset build ==="]

    ae = pd.read_csv(AE_PATH, encoding="utf-8", low_memory=False)
    pkg.append(f"athlete_events: shape={ae.shape}")

    macro = pd.read_csv(MACRO_DS, encoding="utf-8-sig", low_memory=False)
    primary_nocs = set(macro.loc[macro["sample_primary"] == 1, "NOC"].unique())
    pkg.append(f"primary NOCs: {len(primary_nocs)}")

    medals = build_medal_grid(ae)
    pkg.append(f"medal grid: shape={medals.shape} sports={medals['Sport'].nunique()}")

    participation = build_participation_grid(ae)
    pkg.append(f"participation grid: shape={participation.shape}")

    sport_level = build_sport_level(ae)
    pkg.append(f"sport-level features: shape={sport_level.shape}")

    # Sport filter: keep only sports in >= MIN_SPORT_EDITIONS of the 8 primary editions
    sport_ed = medals.groupby("Sport")["Year"].nunique()
    keep_sports = sorted(sport_ed[sport_ed >= MIN_SPORT_EDITIONS].index.tolist())
    pkg.append(f"sports kept (>= {MIN_SPORT_EDITIONS} of {len(PRIMARY_YEARS)} editions): {len(keep_sports)}")
    pkg.append("  " + ", ".join(keep_sports))

    # Full cross-product grid: NOC x Year x Sport
    idx = pd.MultiIndex.from_product(
        [sorted(primary_nocs), PRIMARY_YEARS, keep_sports],
        names=["NOC", "Year", "Sport"],
    ).to_frame(index=False)
    pkg.append(f"full grid: shape={idx.shape}")

    # Merge medals (fill 0 for non-medals)
    df = idx.merge(medals, on=["NOC", "Year", "Sport"], how="left")
    df["medals_in_sport"] = df["medals_in_sport"].fillna(0).astype(int)
    pkg.append(f"after medal merge: medals mean={df['medals_in_sport'].mean():.3f} "
               f"zero_share={(df['medals_in_sport'] == 0).mean():.3f}")

    # Merge participation
    df = df.merge(participation, on=["NOC", "Year", "Sport"], how="left")
    df["n_athletes_in_sport"] = df["n_athletes_in_sport"].fillna(0).astype(int)
    df["country_sent_athletes_in_sport"] = (df["n_athletes_in_sport"] > 0).astype(int)
    pkg.append(f"after participation merge: "
               f"participation_rate={df['country_sent_athletes_in_sport'].mean():.3f}")

    # Merge sport-level
    df = df.merge(sport_level, on=["Year", "Sport"], how="left")
    df["sport_n_events"] = df["sport_n_events"].fillna(0).astype(int)
    pkg.append(f"after sport-level merge: sport_n_events mean={df['sport_n_events'].mean():.1f}")

    # Merge country-level macro
    macro_slim = macro[["NOC", "Year"] + MACRO_FEATURES + ["sample_primary"]].copy()
    df = df.merge(macro_slim, on=["NOC", "Year"], how="left")
    pkg.append(f"after macro merge: shape={df.shape}")

    # Merge sport RCA (variant=total, window=last4)
    disc = pd.read_csv(DISC_SPORT, encoding="utf-8-sig", low_memory=False)
    disc_total = disc[
        (disc["variant"] == "total") & (disc["window"] == "last4")
    ][["NOC", "Year", "Sport", "rca", "medals"]].copy()
    disc_total = disc_total.rename(columns={"rca": "rca_sport", "medals": "prior_medals_sport"})
    df = df.merge(disc_total, on=["NOC", "Year", "Sport"], how="left")
    df["rca_sport"] = df["rca_sport"].fillna(0.0)
    df["prior_medals_sport"] = df["prior_medals_sport"].fillna(0).astype(int)
    pkg.append(f"after RCA merge: rca non-zero rate={(df['rca_sport'] > 0).mean():.3f}")

    # Lag of medals_in_sport (previous edition, per NOC x Sport)
    df = df.sort_values(["NOC", "Sport", "Year"]).reset_index(drop=True)
    df["lag_medals_in_sport"] = (
        df.groupby(["NOC", "Sport"])["medals_in_sport"].shift(1).fillna(0).astype(int)
    )
    pkg.append(f"after lag: shape={df.shape}")

    # Order columns
    col_order = [
        "NOC", "Year", "Sport",
        "medals_in_sport", "lag_medals_in_sport",
        "n_athletes_in_sport", "country_sent_athletes_in_sport",
        "sport_n_events", "rca_sport", "prior_medals_sport",
    ] + MACRO_FEATURES + ["sample_primary"]
    df = df[col_order].copy()

    # Save
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    pkg.append(f"\nper_sport_dataset.csv saved: shape={df.shape}")
    pkg.append(f"columns: {list(df.columns)}")

    # Diagnostics
    pkg.append("\n=== zero share by year ===")
    for y in PRIMARY_YEARS:
        sub = df[df["Year"] == y]
        pkg.append(f"  {y}: n={len(sub):>6d}  zero_share={(sub['medals_in_sport'] == 0).mean():.3f}  "
                   f"mean={sub['medals_in_sport'].mean():.3f}")

    pkg.append("\n=== diagnostics per sport (top 8 by mean medals) ===")
    sport_stats = df.groupby("Sport").agg(
        mean_medals=("medals_in_sport", "mean"),
        total_medals=("medals_in_sport", "sum"),
        n_events=("sport_n_events", "mean"),
        participation_rate=("country_sent_athletes_in_sport", "mean"),
    ).sort_values("total_medals", ascending=False).head(8)
    pkg.append(sport_stats.round(3).to_string())

    pkg.append("\n=== diagnostics per sport (bottom 8 by mean medals) ===")
    sport_stats_low = df.groupby("Sport").agg(
        mean_medals=("medals_in_sport", "mean"),
        total_medals=("medals_in_sport", "sum"),
        n_events=("sport_n_events", "mean"),
        participation_rate=("country_sent_athletes_in_sport", "mean"),
    ).sort_values("total_medals", ascending=True).head(8)
    pkg.append(sport_stats_low.round(3).to_string())

    # Sanity: sum of per-sport medals per (NOC,Year) vs mt_total
    pkg.append("\n=== Sanity check: sum of per-sport medals vs mt_total ===")
    total_per_noc_year = df.groupby(["NOC", "Year"])["medals_in_sport"].sum().rename("sum_sports").reset_index()
    check = total_per_noc_year.merge(
        macro[["NOC", "Year", "mt_total", "sample_primary"]], on=["NOC", "Year"], how="inner"
    )
    check = check[check["sample_primary"] == 1]
    check["diff"] = check["mt_total"] - check["sum_sports"]
    for y in PRIMARY_YEARS:
        sub = check[check["Year"] == y]
        if len(sub) == 0:
            continue
        pkg.append(f"  {y}: mean_diff={sub['diff'].mean():+.2f}  "
                   f"max_diff={sub['diff'].max():.0f}  "
                   f"rows_with_diff_gt5={(sub['diff'] > 5).sum()}")

    # Save report
    report = REPORTS / "phase7c_persport_build.md"
    with open(report, "w", encoding="utf-8") as f:
        f.write("# Chapter 3.5 — per-sport dataset build\n\n")
        f.write("```\n" + "\n".join(pkg) + "\n```\n")

    print("\n" + "=" * 60)
    print("PACKAGE_FOR_CHAT_BEGIN")
    print("=" * 60)
    for line in pkg:
        print(line)
    print("=" * 60)
    print("PACKAGE_FOR_CHAT_END")
    print("=" * 60)


if __name__ == "__main__":
    main()
