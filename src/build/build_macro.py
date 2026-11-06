"""
build_macro.py
===============
Build the Summer NOC x edition panel:
- target (target variable) from medal_table_summary
- features from athlete_events
"""

from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW = PROJECT_ROOT / "data" / "raw"
PROCESSED = PROJECT_ROOT / "data" / "processed"
REPORTS = PROJECT_ROOT / "reports"
PROCESSED.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

AE_PATH = RAW / "athlete_events_through_2026.csv"
MT_PATH = RAW / "medal_table_summary.csv"

NON_STANDARD_NOCS = {
    "URS","GDR","TCH","YUG","FRG","SCG","ANZ","BOH",
    "EUN","ROC","IOA","AIN","EOR","EUA","UAR",
    "AHO","SAA","YMD","YAR","NBO","NFL","CRT","WIF",
}

KEY_YEARS = [1960, 1980, 1988, 1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024]


def build():
    package = []
    print("loading...")
    ae = pd.read_csv(AE_PATH, encoding="utf-8", low_memory=False)
    mt = pd.read_csv(MT_PATH, encoding="utf-8", low_memory=False)
    package.append("raw ae shape: %s" % str(ae.shape))
    package.append("raw mt shape: %s" % str(mt.shape))

    ae = ae[ae["Season"] == "Summer"].copy()
    mt = mt[mt["season"] == "Summer"].copy()
    package.append("summer ae rows: %d  summer mt rows: %d" % (len(ae), len(mt)))

    print("aggregating features...")
    total = ae.groupby(["NOC","Year"]).agg(
        athletes=("ID","nunique"),
        sports=("Sport","nunique"),
        events=("Event","nunique"),
    ).reset_index()

    female = ae[ae["Sex"]=="F"].groupby(["NOC","Year"])["ID"].nunique().rename("female_athletes").reset_index()
    male   = ae[ae["Sex"]=="M"].groupby(["NOC","Year"])["ID"].nunique().rename("male_athletes").reset_index()

    aem = ae.dropna(subset=["Medal"]).drop_duplicates(subset=["NOC","Year","Event","Medal"]).copy()
    aem_g = aem.groupby(["NOC","Year"]).agg(
        ae_total_medals=("Event","size"),
        ae_gold=("Medal", lambda s: (s=="Gold").sum()),
        ae_silver=("Medal", lambda s: (s=="Silver").sum()),
        ae_bronze=("Medal", lambda s: (s=="Bronze").sum()),
    ).reset_index()

    feats = total.merge(female, on=["NOC","Year"], how="left") \
                 .merge(male, on=["NOC","Year"], how="left") \
                 .merge(aem_g, on=["NOC","Year"], how="left")
    for c in ["female_athletes","male_athletes","ae_total_medals","ae_gold","ae_silver","ae_bronze"]:
        feats[c] = feats[c].fillna(0).astype(int)
    feats["female_share"] = (feats["female_athletes"] / feats["athletes"].replace(0, np.nan)).round(4)

    mt2 = mt[["year","noc","country","gold","silver","bronze","total"]].rename(columns={
        "year":"Year","noc":"NOC","gold":"mt_gold","silver":"mt_silver",
        "bronze":"mt_bronze","total":"mt_total","country":"country_name",
    })
    mt2["has_mt_row"] = True

    panel = feats.merge(mt2, on=["NOC","Year"], how="left")
    panel["has_mt_row"] = panel["has_mt_row"].fillna(False).astype(bool)
    for c in ["mt_gold","mt_silver","mt_bronze","mt_total"]:
        panel[c] = panel[c].fillna(0).astype(int)
    panel["is_non_standard_noc"] = panel["NOC"].isin(NON_STANDARD_NOCS)
    panel = panel.sort_values(["Year","NOC"]).reset_index(drop=True)

    cov = panel.groupby("Year").agg(
        n_noc_participating=("NOC","nunique"),
        n_noc_with_mt_row=("has_mt_row","sum"),
        total_athletes=("athletes","sum"),
        total_medals_mt=("mt_total","sum"),
        total_medals_ae=("ae_total_medals","sum"),
        sum_female=("female_athletes","sum"),
        sum_male=("male_athletes","sum"),
    ).reset_index()
    cov["female_share"] = (cov["sum_female"] / (cov["sum_female"]+cov["sum_male"])).round(3)
    cov["gap_medals_mt_minus_ae"] = cov["total_medals_mt"] - cov["total_medals_ae"]

    ae_pairs = set(zip(feats["NOC"], feats["Year"]))
    mt_only = []
    for _, row in mt2.iterrows():
        if (row["NOC"], row["Year"]) not in ae_pairs:
            mt_only.append((row["NOC"], int(row["Year"]), int(row["mt_total"])))

    ae_nocs = set(feats["NOC"].unique())
    mt_nocs = set(mt2["NOC"].unique())
    only_in_mt = sorted(mt_nocs - ae_nocs)
    only_in_ae = sorted(ae_nocs - mt_nocs)

    ns_present = sorted(panel.loc[panel["is_non_standard_noc"], "NOC"].unique().tolist())

    panel_out = PROCESSED / "panel_summer_macro.csv"
    panel.to_csv(panel_out, index=False, encoding="utf-8-sig")
    cov_out = REPORTS / "phase1_coverage_matrix.csv"
    cov.to_csv(cov_out, index=False, encoding="utf-8-sig")

    package.append("\npanel shape: %s" % str(panel.shape))
    package.append("panel columns: %s" % str(list(panel.columns)))
    package.append("\npanel head(3):")
    package.append(panel.head(3).to_string())

    package.append("\nnull rates in panel (top 10):")
    package.append(panel.isna().mean().sort_values(ascending=False).head(10).round(3).to_string())

    package.append("\ncoverage matrix (key years):")
    package.append("year  n_noc  n_mt  total_ath  mt_medals  ae_medals  gap  fem_share")
    for _, r in cov.iterrows():
        if int(r["Year"]) in KEY_YEARS:
            package.append("  %d   %4d  %4d  %7d  %8d  %8d  %4d  %.2f" % (
                int(r["Year"]), int(r["n_noc_participating"]), int(r["n_noc_with_mt_row"]),
                int(r["total_athletes"]), int(r["total_medals_mt"]),
                int(r["total_medals_ae"]), int(r["gap_medals_mt_minus_ae"]),
                float(r["female_share"]),
            ))

    package.append("\nnon-standard NOCs in panel: %s" % ns_present)
    package.append("\nNOCs in mt but not in ae (overall): %s" % only_in_mt)
    package.append("NOCs in ae but not in mt (overall): first 20 of %d" % len(only_in_ae))
    package.append(str(only_in_ae[:20]))

    package.append("\nmt-only (NOC, Year) pairs missing from ae: %d" % len(mt_only))
    package.append(str(mt_only[:10]))

    package.append("\nfiles saved:")
    package.append("  panel: %s" % panel_out)
    package.append("  coverage: %s" % cov_out)

    print("\n" + "=" * 60)
    print("PACKAGE_FOR_CHAT_BEGIN")
    print("=" * 60)
    for line in package:
        print(line)
    print("=" * 60)
    print("PACKAGE_FOR_CHAT_END")
    print("=" * 60)


if __name__ == "__main__":
    build()
