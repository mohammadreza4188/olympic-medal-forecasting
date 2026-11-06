"""
build_women_features.py
========================
Enrich model_dataset.csv with gender-specific features for Chapter 3.2.

Features added (all lagged or participation-based, no leakage):
- log_female_athletes: log1p of female_athletes (already in panel)
- lag_female_medal_share: female_medal_share from previous edition
- female_athletes_ratio_of_total: female_athletes / athletes (already = female_share)
- female_athletes_to_pop_ratio: female_athletes / population (talent pool proxy)

NOTE: same-edition female_medal_share is NOT added to the model —
it is derived from the target and would be leakage.
The column female_medal_share_current is stored ONLY for descriptive tables.

See references/ch03_women_protocol.md (to be written in same phase).
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

AE_PATH = RAW / "athlete_events_through_2026.csv"
DATASET_IN = PROCESSED / "model_dataset.csv"
DATASET_OUT = PROCESSED / "model_dataset_women.csv"


def compute_gender_medals_from_ae(ae):
    """Per (NOC, Year): female and male medal counts (de-duped like Phase 4b)."""
    ae = ae[ae["Season"] == "Summer"].copy()
    ae = ae[ae["Medal"].notna()].copy()
    ae = ae.drop_duplicates(subset=["NOC", "Year", "Sport", "Event", "Medal"])

    g = ae.groupby(["NOC", "Year", "Sex"]).size().rename("n_medals").reset_index()
    piv = g.pivot_table(index=["NOC", "Year"], columns="Sex", values="n_medals",
                        fill_value=0).reset_index()
    piv = piv.rename(columns={"F": "ae_female_medals", "M": "ae_male_medals"})
    piv = piv.fillna(0)
    total = piv["ae_female_medals"] + piv["ae_male_medals"]
    piv["female_medal_share_current"] = np.where(
        total > 0, piv["ae_female_medals"] / total, np.nan
    )
    return piv


def main():
    pkg = []
    pkg.append("=== Chapter 3.2: Women's feature build ===")

    df = pd.read_csv(DATASET_IN, encoding="utf-8-sig", low_memory=False)
    pkg.append(f"model_dataset: shape={df.shape}")

    ae = pd.read_csv(AE_PATH, encoding="utf-8", low_memory=False)
    gender_medals = compute_gender_medals_from_ae(ae)
    pkg.append(f"gender_medals: shape={gender_medals.shape}")

    df = df.merge(gender_medals, on=["NOC", "Year"], how="left")
    df["ae_female_medals"] = df["ae_female_medals"].fillna(0).astype(int)
    df["ae_male_medals"] = df["ae_male_medals"].fillna(0).astype(int)

    # Lag features (previous edition) — safe
    df = df.sort_values(["NOC", "Year"]).reset_index(drop=True)
    df["lag_female_medal_share_raw"] = (
        df.groupby("NOC")["female_medal_share_current"].shift(1)
    )
    df["lag_female_medal_share_missing"] = (
        df["lag_female_medal_share_raw"].isna().astype(int)
    )
    df["lag_female_medal_share"] = df["lag_female_medal_share_raw"].fillna(0)
    df["lag_female_medals"] = (
        df.groupby("NOC")["ae_female_medals"].shift(1).fillna(0).astype(int)
    )
    df["lag_male_medals"] = (
        df.groupby("NOC")["ae_male_medals"].shift(1).fillna(0).astype(int)
    )

    # Derived features
    df["log_female_athletes"] = np.log1p(df["female_athletes"].clip(lower=0))
    df["female_athletes_to_pop_ratio"] = np.where(
        df["population_avg4y"] > 0,
        df["female_athletes"] / df["population_avg4y"],
        np.nan,
    )

    df.to_csv(DATASET_OUT, index=False, encoding="utf-8-sig")
    pkg.append(f"\nmodel_dataset_women.csv saved: shape={df.shape}")

    # Coverage check
    new_cols = [
        "lag_female_medal_share", "log_female_athletes",
        "female_athletes_to_pop_ratio", "lag_female_medals", "lag_male_medals",
    ]
    prim = df[df["sample_primary"] == 1]
    pkg.append("\nnull rates in primary sample:")
    pkg.append(prim[new_cols].isna().mean().round(3).to_string())

    pkg.append("\ndescriptive: female_share over recent editions (primary):")
    for y in [1996, 2004, 2012, 2020, 2024]:
        sub = prim[prim["Year"] == y]
        if len(sub):
            pkg.append(
                f"  {y}: n={len(sub)}  mean_female_share={sub['female_share'].mean():.3f}  "
                f"mean_female_medals={sub['ae_female_medals'].mean():.2f}"
            )

    report_path = ROOT / "reports" / "phase7a_women_features.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Chapter 3.2 — Women's feature build\n\n")
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
