"""
train_eval_per_sport.py
=======================
Chapter 3.5 evaluation: per-sport modeling + aggregation vs direct vs naive.

For each test year Y:
  1. Train a per-sport XGB model on (NOC, Year<Y, Sport) data
  2. Predict medals_in_sport for (NOC, Y, Sport)
  3. Sum across sports to get predicted_total
  4. Train M1 direct (10 macro features, XGB) for comparison
  5. Compare RMSE: M0 naive, M1 direct, Aggregation

Primary test years: 2012, 2016 (clean).
Sensitivity: 2020, 2024 (contaminated by 74-event attribution gap).

See references/ch05_persport_protocol.md
"""

import random
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

PER_SPORT = PROCESSED / "per_sport_dataset.csv"
MACRO_DS = PROCESSED / "model_dataset_team.csv"

PER_SPORT_FEATURES = [
    "lag_medals_in_sport", "n_athletes_in_sport", "country_sent_athletes_in_sport",
    "sport_n_events", "rca_sport", "prior_medals_sport",
    "log_gdp_const_avg4y", "log_gdp_pcap_const_avg4y", "log_population_avg4y",
    "athletes", "events", "female_share", "host", "lag_mt_total",
]
MACRO_FEATURES = [
    "log_gdp_const_avg4y", "log_gdp_pcap_const_avg4y", "log_population_avg4y",
    "athletes", "sports", "events", "female_share", "host",
    "lag_mt_total", "lag_mt_gold",
]

MIN_POSITIVE_SAMPLES = 10
PRIMARY_TEST_YEARS = [2012, 2016]
SENSITIVITY_TEST_YEARS = [2020, 2024]
ALL_TEST_YEARS = PRIMARY_TEST_YEARS + SENSITIVITY_TEST_YEARS


def fit_xgb_count(X_tr, y_tr):
    m = XGBRegressor(
        n_estimators=300, max_depth=3, learning_rate=0.05,
        objective="count:poisson", random_state=SEED,
        verbosity=0, n_jobs=-1, min_child_weight=3,
    )
    m.fit(X_tr, y_tr)
    return m


def rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def log_rmse(a, b):
    a = np.asarray(a, dtype=float)
    b = np.clip(np.asarray(b, dtype=float), 0, None)
    return float(np.sqrt(np.mean((np.log1p(a) - np.log1p(b)) ** 2)))


def spearman(a, b):
    if len(a) < 2:
        return np.nan
    return float(spearmanr(a, b).statistic)


def main():
    pkg = ["=== Chapter 3.5: per-sport evaluation ==="]

    per_sport = pd.read_csv(PER_SPORT, encoding="utf-8-sig", low_memory=False)
    macro = pd.read_csv(MACRO_DS, encoding="utf-8-sig", low_memory=False)
    primary_nocs = set(macro.loc[macro["sample_primary"] == 1, "NOC"].unique())
    per_sport = per_sport[per_sport["NOC"].isin(primary_nocs)].copy()

    pkg.append(f"per_sport dataset: shape={per_sport.shape}  sports={per_sport['Sport'].nunique()}")
    pkg.append(f"macro dataset: shape={macro.shape}")

    # Country-level ground truth
    truth = macro[macro["sample_primary"] == 1][["NOC", "Year", "mt_total", "lag_mt_total"]].copy()
    truth = truth.rename(columns={"lag_mt_total": "naive_prediction"})

    all_results = []
    per_sport_preds_log = []  # store per-sport predictions per test year

    for Y in ALL_TEST_YEARS:
        tag = "PRIMARY" if Y in PRIMARY_TEST_YEARS else "SENSITIVITY"
        pkg.append(f"\n{'='*60}\n=== TEST YEAR {Y} ({tag}) ===\n{'='*60}")

        # ---------- Macro direct (M1) ----------
        tr_macro = macro[(macro["Year"] < Y) & (macro["sample_primary"] == 1)].dropna(subset=MACRO_FEATURES)
        te_macro = macro[(macro["Year"] == Y) & (macro["sample_primary"] == 1)].copy()
        if len(tr_macro) < 20 or len(te_macro) == 0:
            pkg.append(f"  skip: insufficient macro rows")
            continue

        X_tr_m = tr_macro[MACRO_FEATURES].values
        y_tr_m = tr_macro["mt_total"].values
        X_te_m = te_macro[MACRO_FEATURES].values

        m_macro = fit_xgb_count(X_tr_m, y_tr_m)
        pred_macro = np.clip(m_macro.predict(X_te_m), 0, None)

        # ---------- Per-sport aggregation ----------
        tr_sport_all = per_sport[(per_sport["Year"] < Y) & (per_sport["sample_primary"] == 1)].copy()
        te_sport_all = per_sport[(per_sport["Year"] == Y) & (per_sport["sample_primary"] == 1)].copy()

        if len(tr_sport_all) < 100 or len(te_sport_all) == 0:
            pkg.append(f"  skip: insufficient per-sport rows")
            continue

        sports = sorted(te_sport_all["Sport"].unique())
        pred_per_sport_frames = []
        n_fallback = 0
        n_trained = 0

        for sport in sports:
            tr_s = tr_sport_all[tr_sport_all["Sport"] == sport].dropna(subset=PER_SPORT_FEATURES)
            te_s = te_sport_all[te_sport_all["Sport"] == sport].copy()

            if len(tr_s) < 30 or len(te_s) == 0:
                # Not enough training; predict 0
                te_s["pred_medals_sport"] = 0.0
                n_fallback += 1
                pred_per_sport_frames.append(te_s[["NOC", "Sport", "pred_medals_sport"]])
                continue

            y_tr_s = tr_s["medals_in_sport"].values
            if (y_tr_s > 0).sum() < MIN_POSITIVE_SAMPLES:
                te_s["pred_medals_sport"] = 0.0
                n_fallback += 1
                pred_per_sport_frames.append(te_s[["NOC", "Sport", "pred_medals_sport"]])
                continue

            X_tr_s = tr_s[PER_SPORT_FEATURES].values
            X_te_s = te_s[PER_SPORT_FEATURES].values
            try:
                m = fit_xgb_count(X_tr_s, y_tr_s)
                pred = np.clip(m.predict(X_te_s), 0, None)
                te_s["pred_medals_sport"] = pred
                n_trained += 1
            except Exception as e:
                te_s["pred_medals_sport"] = 0.0
                n_fallback += 1
            pred_per_sport_frames.append(te_s[["NOC", "Sport", "pred_medals_sport"]])

        pkg.append(f"  sports trained: {n_trained}, fallback (predict 0): {n_fallback}")

        pred_per_sport = pd.concat(pred_per_sport_frames, ignore_index=True)
        pred_agg = (
            pred_per_sport.groupby("NOC")["pred_medals_sport"]
            .sum()
            .rename("agg_prediction")
            .reset_index()
        )

        # ---------- Merge all predictions ----------
        comp = truth[truth["Year"] == Y].copy()
        comp = comp.merge(
            te_macro[["NOC"]].assign(macro_prediction=pred_macro),
            on="NOC", how="left",
        )
        comp = comp.merge(pred_agg, on="NOC", how="left")
        comp["macro_prediction"] = comp["macro_prediction"].fillna(0)
        comp["agg_prediction"] = comp["agg_prediction"].fillna(0)

        y = comp["mt_total"].values
        m0 = comp["naive_prediction"].values.astype(float)
        m1 = comp["macro_prediction"].values.astype(float)
        agg = comp["agg_prediction"].values.astype(float)

        # ---------- Metrics ----------
        results_y = {
            "edition": Y,
            "tag": tag,
            "n_noc": len(comp),
            "M0_rmse": rmse(y, m0), "M0_log_rmse": log_rmse(y, m0), "M0_rho": spearman(y, m0),
            "M1_rmse": rmse(y, m1), "M1_log_rmse": log_rmse(y, m1), "M1_rho": spearman(y, m1),
            "AGG_rmse": rmse(y, agg), "AGG_log_rmse": log_rmse(y, agg), "AGG_rho": spearman(y, agg),
        }
        results_y["AGG_vs_M0_pct"] = (results_y["M0_rmse"] - results_y["AGG_rmse"]) / results_y["M0_rmse"] * 100
        results_y["AGG_vs_M1_pct"] = (results_y["M1_rmse"] - results_y["AGG_rmse"]) / results_y["M1_rmse"] * 100
        results_y["M1_vs_M0_pct"] = (results_y["M0_rmse"] - results_y["M1_rmse"]) / results_y["M0_rmse"] * 100
        all_results.append(results_y)

        pkg.append(f"\n  metric        M0       M1       AGG")
        pkg.append(f"  RMSE      {results_y['M0_rmse']:8.3f} {results_y['M1_rmse']:8.3f} {results_y['AGG_rmse']:8.3f}")
        pkg.append(f"  log_RMSE  {results_y['M0_log_rmse']:8.3f} {results_y['M1_log_rmse']:8.3f} {results_y['AGG_log_rmse']:8.3f}")
        pkg.append(f"  Spearman  {results_y['M0_rho']:8.3f} {results_y['M1_rho']:8.3f} {results_y['AGG_rho']:8.3f}")
        pkg.append(f"\n  AGG vs M0: {results_y['AGG_vs_M0_pct']:+.1f}%")
        pkg.append(f"  AGG vs M1: {results_y['AGG_vs_M1_pct']:+.1f}%")
        pkg.append(f"  M1  vs M0: {results_y['M1_vs_M0_pct']:+.1f}%")

        # Store predictions for error-correlation analysis
        per_sport_preds_log.append({
            "edition": Y,
            "pred_per_sport": pred_per_sport.copy(),
            "comp": comp.copy(),
        })

    # ---------- Aggregate ----------
    res = pd.DataFrame(all_results)
    res.to_csv(REPORTS / "phase7c_persport_results.csv", index=False)

    pkg.append("\n" + "=" * 60)
    pkg.append("=== AGGREGATE SUMMARY ===")
    pkg.append("=" * 60)
    pkg.append(res[["edition", "tag", "M0_rmse", "M1_rmse", "AGG_rmse",
                    "AGG_vs_M0_pct", "AGG_vs_M1_pct", "M1_vs_M0_pct"]].round(3).to_string(index=False))

    pkg.append("\n=== PRIMARY TEST YEARS (2012, 2016) ===")
    prim = res[res["tag"] == "PRIMARY"]
    pkg.append(f"  mean M1_vs_M0:  {prim['M1_vs_M0_pct'].mean():+.1f}%")
    pkg.append(f"  mean AGG_vs_M0: {prim['AGG_vs_M0_pct'].mean():+.1f}%")
    pkg.append(f"  mean AGG_vs_M1: {prim['AGG_vs_M1_pct'].mean():+.1f}%")
    n_agg_beats_m0 = (prim["AGG_vs_M0_pct"] > 0).sum()
    n_agg_beats_m1 = (prim["AGG_vs_M1_pct"] > 0).sum()
    pkg.append(f"  AGG beats M0 in {n_agg_beats_m0}/{len(prim)} editions")
    pkg.append(f"  AGG beats M1 in {n_agg_beats_m1}/{len(prim)} editions")

    # ---------- H4a verdict ----------
    pkg.append("\n=== H4a verdict (pre-registered) ===")
    h4a_1 = n_agg_beats_m0 >= 3 or (n_agg_beats_m0 >= 2 and len(prim) == 2)
    h4a_2 = n_agg_beats_m1 >= 2 or (n_agg_beats_m1 >= 1 and len(prim) == 2)
    if h4a_1 and h4a_2:
        pkg.append("  VERDICT: H4a SUPPORTED (aggregation beats naive and direct)")
    else:
        pkg.append("  VERDICT: H4a NOT SUPPORTED")

    # ---------- H4c: error correlation diagnostic ----------
    pkg.append("\n=== H4c: per-sport error correlation diagnostic ===")
    pkg.append("If H4a fails, we test whether errors of per-sport predictions are correlated.")
    for entry in per_sport_preds_log:
        Y = entry["edition"]
        if Y not in PRIMARY_TEST_YEARS:
            continue
        pred_per_sport = entry["pred_per_sport"]
        te_macro = macro[(macro["Year"] == Y) & (macro["sample_primary"] == 1)][["NOC"]].copy()

        # Ground truth per (NOC, Sport)
        truth_sport = per_sport[(per_sport["Year"] == Y) & (per_sport["sample_primary"] == 1)][
            ["NOC", "Sport", "medals_in_sport"]
        ].copy()
        merged = pred_per_sport.merge(truth_sport, on=["NOC", "Sport"], how="inner")
        merged["error"] = merged["pred_medals_sport"] - merged["medals_in_sport"]

        # Correlate errors across sports for a few NOCs
        # Compute per-NOC mean error and per-NOC error variance
        per_noc = merged.groupby("NOC")["error"].agg(["mean", "std", "count"]).reset_index()
        per_noc = per_noc[per_noc["count"] >= 5]

        # Correlation between team-vs-individual errors as a proxy for shared signal
        # Better: for top-5 countries, compute the correlation of errors across sports
        top5 = macro[(macro["Year"] == Y) & (macro["sample_primary"] == 1)].nlargest(5, "mt_total")["NOC"].tolist()

        for noc in top5:
            noc_err = merged[merged["NOC"] == noc].sort_values("Sport")["error"].values
            if len(noc_err) < 5:
                continue
            # autocorrelation proxy: split in half, correlate halves
            half = len(noc_err) // 2
            if half >= 3:
                try:
                    r, _ = pearsonr(noc_err[:half], noc_err[half:])
                except Exception:
                    r = np.nan
            else:
                r = np.nan
            pkg.append(f"  {Y}  {noc}: n_sports={len(noc_err)}, "
                       f"mean_err={noc_err.mean():+.3f}, err_std={noc_err.std():.3f}, "
                       f"split-half_corr={r:+.2f}" if not np.isnan(r) else
                       f"  {Y}  {noc}: n_sports={len(noc_err)}, mean_err={noc_err.mean():+.3f}")

    # ---------- H4b: specialization subgroup (preliminary) ----------
    pkg.append("\n=== H4b: specialization subgroup (preliminary) ===")
    pkg.append("Split countries by rca_max in any sport; compare aggregation gains.")
    for entry in per_sport_preds_log:
        Y = entry["edition"]
        if Y not in PRIMARY_TEST_YEARS:
            continue
        comp = entry["comp"].copy()
        # Merge rca_max from macro
        rca_info = per_sport[per_sport["Year"] == Y].groupby("NOC")["rca_sport"].max().rename("rca_max").reset_index()
        comp = comp.merge(rca_info, on="NOC", how="left")
        comp["rca_max"] = comp["rca_max"].fillna(0)
        comp["specialized"] = (comp["rca_max"] > 1.5).astype(int)

        for spec_val in [0, 1]:
            sub = comp[comp["specialized"] == spec_val]
            if len(sub) < 10:
                continue
            agg_gain = (rmse(sub["mt_total"], sub["naive_prediction"])
                        - rmse(sub["mt_total"], sub["agg_prediction"]))
            pkg.append(f"  {Y}  specialized={spec_val}: n={len(sub)}, "
                       f"AGG_vs_M0_RMSE_gain={agg_gain:+.3f}")

    report = REPORTS / "phase7c_persport_results.md"
    with open(report, "w", encoding="utf-8") as f:
        f.write("# Chapter 3.5 — per-sport evaluation\n\n")
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
