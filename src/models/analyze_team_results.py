"""
analyze_team_results.py
=======================
Post-hoc analysis on phase7b_team_results.csv:
- H3b: relative RMSE improvement over naive (fixed M0 broadcast)
- H3c: female_share marginal association with each target
- Bonus: aggregation test (team_pred + individual_pred vs direct total)

Reads the existing CSV, refits XGB only for H3c importance, and refits RF
only for the aggregation test. Fast (~10s).
"""

import random
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

RESULTS_CSV = REPORTS / "phase7b_team_results.csv"
DATASET = PROCESSED / "model_dataset_team.csv"

MACRO_NO_LAG = [
    "log_gdp_const_avg4y", "log_gdp_pcap_const_avg4y", "log_population_avg4y",
    "athletes", "sports", "events", "female_share", "host",
]
VARIANTS = {
    "team_medals": {
        "M1":      MACRO_NO_LAG + ["lag_team_medals", "lag_mt_gold"],
        "M1_noLag": MACRO_NO_LAG,
    },
    "individual_medals": {
        "M1":      MACRO_NO_LAG + ["lag_individual_medals", "lag_mt_gold"],
        "M1_noLag": MACRO_NO_LAG,
    },
}
TEST_YEARS_PER_TARGET = {
    "team_medals":       [2012, 2016],
    "individual_medals": [2012, 2016, 2020, 2024],
}


def main():
    pkg = ["=== Chapter 3.4 post-hoc analysis ==="]

    res = pd.read_csv(RESULTS_CSV, encoding="utf-8-sig", low_memory=False)
    pkg.append(f"loaded results: shape={res.shape}")

    # ------------------------------------------------------------------ H3b
    pkg.append("\n=== H3b: relative RMSE improvement over naive (corrected) ===")
    pivot = res.pivot_table(
        index=["target", "edition", "family"], columns="variant", values="rmse"
    ).reset_index()

    m0_map = res[res["family"] == "naive"].set_index(["target", "edition"])["rmse"].to_dict()
    pivot["M0"] = pivot.apply(
        lambda r: m0_map.get((r["target"], r["edition"]), float("nan")), axis=1
    )

    for target in ["team_medals", "individual_medals"]:
        sub = pivot[(pivot["target"] == target) & (pivot["family"] != "naive")].copy()
        if len(sub) == 0:
            continue
        sub["M1_gap"] = (sub["M0"] - sub["M1"]) / sub["M0"] * 100
        sub["M1_noLag_gap"] = (sub["M0"] - sub["M1_noLag"]) / sub["M0"] * 100
        pkg.append(f"\n--- {target} ({sub['edition'].nunique()} test editions) ---")
        pkg.append(f"  {'family':<8s}  {'M1_gap':>10s}  {'M1_noLag_gap':>13s}")
        for fam in ["poisson", "hurdle", "rf", "xgb"]:
            fs = sub[sub["family"] == fam]
            if len(fs) == 0:
                continue
            pkg.append(
                f"  {fam:<8s}  {fs['M1_gap'].mean():>+9.1f}%  "
                f"{fs['M1_noLag_gap'].mean():>+12.1f}%"
            )

    # ------------------------------------------------------------------ H3c
    df = pd.read_csv(DATASET, encoding="utf-8-sig", low_memory=False)
    primary = df[df["sample_primary"] == 1].copy()
    pkg.append(f"\n=== H3c: female_share marginal association ===")
    pkg.append("(Pearson r on primary sample + XGB feature importance)")

    for target in ["team_medals", "individual_medals"]:
        vals = primary[[target, "female_share"]].dropna()
        if len(vals) < 10:
            continue
        r, p = pearsonr(vals["female_share"], vals[target])
        pkg.append(f"\n  {target}:")
        pkg.append(f"    Pearson r = {r:+.3f}  (p = {p:.2e}, n = {len(vals)})")

        feats = VARIANTS[target]["M1"]
        test_years = TEST_YEARS_PER_TARGET[target]
        female_idx = feats.index("female_share")
        for Y in test_years:
            trv = primary[primary["Year"] < Y].dropna(subset=feats)
            if len(trv) < 20:
                continue
            m = XGBRegressor(
                n_estimators=400, max_depth=4, learning_rate=0.05,
                objective="count:poisson", random_state=SEED,
                verbosity=0, n_jobs=-1,
            )
            m.fit(trv[feats].values, trv[target].values)
            imp = m.feature_importances_
            rank = int(np.where(np.argsort(-imp) == female_idx)[0][0]) + 1
            pkg.append(
                f"    {Y}: female_share rank = {rank}/{len(feats)}, "
                f"importance = {imp[female_idx]:.3f}"
            )

    # ---------------------------------------------------- Aggregation test
    pkg.append("\n=== Bonus: aggregation test (team + individual vs naive) ===")
    pkg.append("Fit RF on team and individual, sum predictions, compare to naive total.")
    pkg.append("Only 2012 and 2016 are valid (2020/2024 team data contaminated).")

    for Y in [2012, 2016]:
        tr = primary[primary["Year"] < Y].copy()
        te = primary[primary["Year"] == Y].copy()
        if len(te) == 0:
            continue

        # Fit RF for both targets on common rows
        team_feats = VARIANTS["team_medals"]["M1"]
        ind_feats = VARIANTS["individual_medals"]["M1"]
        tr_common = tr.dropna(subset=set(team_feats) | set(ind_feats))

        rf_team = RandomForestRegressor(
            n_estimators=300, max_depth=10, min_samples_leaf=3,
            random_state=SEED, n_jobs=-1,
        )
        rf_team.fit(tr_common[team_feats].values, tr_common["team_medals"].values)
        team_pred = np.clip(rf_team.predict(te[team_feats].values), 0, None)

        rf_ind = RandomForestRegressor(
            n_estimators=300, max_depth=10, min_samples_leaf=3,
            random_state=SEED, n_jobs=-1,
        )
        rf_ind.fit(tr_common[ind_feats].values, tr_common["individual_medals"].values)
        ind_pred = np.clip(rf_ind.predict(te[ind_feats].values), 0, None)

        total_pred = team_pred + ind_pred
        y_actual = te["mt_total"].values
        y_naive = te["lag_mt_total"].values.astype(float)

        def rmse(a, b):
            return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))

        rmse_agg = rmse(total_pred, y_actual)
        rmse_naive = rmse(y_naive, y_actual)
        gap = (rmse_naive - rmse_agg) / rmse_naive * 100

        # Sanity: how much of actual total is covered by team+individual?
        covered = (te["team_medals"] + te["individual_medals"]).values
        coverage = float(covered.sum() / y_actual.sum()) if y_actual.sum() > 0 else np.nan

        pkg.append(f"\n  {Y}:")
        pkg.append(f"    actual team+individual coverage of total = {coverage:.3f}")
        pkg.append(f"    RMSE (team+ind sum vs total)  = {rmse_agg:.3f}")
        pkg.append(f"    RMSE (naive vs total)          = {rmse_naive:.3f}")
        pkg.append(f"    naive gap of aggregation       = {gap:+.1f}%")

    # ------------------------------------------------------------------ save
    report = REPORTS / "phase7b_team_posthoc.md"
    with open(report, "w", encoding="utf-8") as f:
        f.write("# Chapter 3.4 post-hoc analysis\n\n")
        f.write("```\n" + "\n".join(pkg) + "\n```\n")

    print("\n" + "=" * 60)
    print("PACKAGE_FOR_CHAT_BEGIN")
    print("=" * 60)
    for line in pkg:
        print(line)
    print("=" * 60)
    print("PACKAGE_FOR_CHAT_END")
    print("=" * 60)
    print(f"\nFull report: {report}")


if __name__ == "__main__":
    main()
