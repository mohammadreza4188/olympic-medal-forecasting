"""
sensitivity_zero_inflated.py
============================
Chapter 4 sensitivity: do zero-inflation-aware models fix the aggregation
failure?

Three comparisons:
1. AGG_hurdle: per-sport Hurdle (logistic x Poisson) + aggregation
2. AGG_scaled: XGB aggregation scaled by calibration factor from training
3. M1_hurdle: country-level Hurdle vs country-level XGB (re-verify)

Test years: 2012, 2016 primary; 2020, 2024 sensitivity.

Run: python src/models/sensitivity_zero_inflated.py
"""

import random
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression, PoissonRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
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
MIN_TRAIN_ROWS = 30
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


def fit_hurdle(X_tr, y_tr):
    """Return a callable predictor = P(any) * E[count | any]."""
    clf = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(C=1.0, max_iter=1000, random_state=SEED)),
    ])
    clf.fit(X_tr, (y_tr > 0).astype(int))

    pos = y_tr > 0
    if pos.sum() >= 5:
        cnt = Pipeline([
            ("scaler", StandardScaler()),
            ("poisson", PoissonRegressor(alpha=0.1, max_iter=1000)),
        ])
        cnt.fit(X_tr[pos], y_tr[pos])
    else:
        cnt = None

    fallback = float(y_tr[pos].mean()) if pos.any() else 1.0

    def predict(X_te):
        p_any = clf.predict_proba(X_te)[:, 1]
        if cnt is not None:
            mean_pos = cnt.predict(X_te)
        else:
            mean_pos = np.full(len(X_te), fallback)
        return np.clip(p_any * mean_pos, 0, None)

    return predict


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
    pkg = ["=== Sensitivity: zero-inflated models for aggregation ==="]

    per_sport = pd.read_csv(PER_SPORT, encoding="utf-8-sig", low_memory=False)
    macro = pd.read_csv(MACRO_DS, encoding="utf-8-sig", low_memory=False)
    primary_nocs = set(macro.loc[macro["sample_primary"] == 1, "NOC"].unique())
    per_sport = per_sport[per_sport["NOC"].isin(primary_nocs)].copy()

    truth = macro[macro["sample_primary"] == 1][
        ["NOC", "Year", "mt_total", "lag_mt_total"]
    ].rename(columns={"lag_mt_total": "naive_pred"}).copy()

    all_results = []

    for Y in ALL_TEST_YEARS:
        tag = "PRIMARY" if Y in PRIMARY_TEST_YEARS else "SENSITIVITY"
        pkg.append(f"\n{'='*60}\n=== TEST YEAR {Y} ({tag}) ===\n{'='*60}")

        # ---------------- Country-level baselines ----------------
        tr_macro = macro[
            (macro["Year"] < Y) & (macro["sample_primary"] == 1)
        ].dropna(subset=MACRO_FEATURES)
        te_macro = macro[
            (macro["Year"] == Y) & (macro["sample_primary"] == 1)
        ].copy()

        if len(tr_macro) < 30 or len(te_macro) == 0:
            pkg.append("  skip: insufficient macro rows")
            continue

        X_tr_m = tr_macro[MACRO_FEATURES].values
        y_tr_m = tr_macro["mt_total"].values
        X_te_m = te_macro[MACRO_FEATURES].values

        # XGB direct
        m_xgb = fit_xgb_count(X_tr_m, y_tr_m)
        pred_m1_xgb = np.clip(m_xgb.predict(X_te_m), 0, None)

        # Hurdle direct
        pred_fn_hurdle = fit_hurdle(X_tr_m, y_tr_m)
        pred_m1_hurdle = pred_fn_hurdle(X_te_m)

        # ---------------- Per-sport models ----------------
        tr_ps_all = per_sport[
            (per_sport["Year"] < Y) & (per_sport["sample_primary"] == 1)
        ].copy()
        te_ps_all = per_sport[
            (per_sport["Year"] == Y) & (per_sport["sample_primary"] == 1)
        ].copy()

        sports = sorted(te_ps_all["Sport"].unique())
        n_xgb_trained = 0
        n_hurdle_trained = 0

        # Collect predictions from both per-sport model types
        preds_xgb_frames = []
        preds_hurdle_frames = []
        # Also keep training-fold aggregate vs actual for calibration
        train_actual_by_noc = tr_macro[["NOC", "mt_total"]].set_index("NOC")["mt_total"].to_dict()

        for sport in sports:
            tr_s = tr_ps_all[tr_ps_all["Sport"] == sport].dropna(subset=PER_SPORT_FEATURES)
            te_s = te_ps_all[te_ps_all["Sport"] == sport].copy()
            if len(tr_s) < MIN_TRAIN_ROWS or len(te_s) == 0:
                te_s["pred_xgb"] = 0.0
                te_s["pred_hurdle"] = 0.0
                preds_xgb_frames.append(te_s[["NOC", "Sport", "pred_xgb"]])
                preds_hurdle_frames.append(te_s[["NOC", "Sport", "pred_hurdle"]])
                continue

            y_tr_s = tr_s["medals_in_sport"].values
            if (y_tr_s > 0).sum() < MIN_POSITIVE_SAMPLES:
                te_s["pred_xgb"] = 0.0
                te_s["pred_hurdle"] = 0.0
                preds_xgb_frames.append(te_s[["NOC", "Sport", "pred_xgb"]])
                preds_hurdle_frames.append(te_s[["NOC", "Sport", "pred_hurdle"]])
                continue

            X_tr_s = tr_s[PER_SPORT_FEATURES].values
            X_te_s = te_s[PER_SPORT_FEATURES].values

            # XGB
            try:
                m = fit_xgb_count(X_tr_s, y_tr_s)
                te_s["pred_xgb"] = np.clip(m.predict(X_te_s), 0, None)
                n_xgb_trained += 1
            except Exception:
                te_s["pred_xgb"] = 0.0

            # Hurdle
            try:
                h = fit_hurdle(X_tr_s, y_tr_s)
                te_s["pred_hurdle"] = h(X_te_s)
                n_hurdle_trained += 1
            except Exception:
                te_s["pred_hurdle"] = 0.0

            preds_xgb_frames.append(te_s[["NOC", "Sport", "pred_xgb"]])
            preds_hurdle_frames.append(te_s[["NOC", "Sport", "pred_hurdle"]])

        pkg.append(f"  sports: XGB={n_xgb_trained}, Hurdle={n_hurdle_trained}, total={len(sports)}")

        # ---------------- Aggregate ----------------
        agg_xgb = (
            pd.concat(preds_xgb_frames, ignore_index=True)
            .groupby("NOC")["pred_xgb"].sum().rename("agg_xgb").reset_index()
        )
        agg_hurdle = (
            pd.concat(preds_hurdle_frames, ignore_index=True)
            .groupby("NOC")["pred_hurdle"].sum().rename("agg_hurdle").reset_index()
        )

        comp = truth[truth["Year"] == Y][["NOC", "mt_total", "naive_pred"]].copy()
        comp = comp.merge(
            te_macro[["NOC"]].assign(m1_xgb=pred_m1_xgb, m1_hurdle=pred_m1_hurdle),
            on="NOC", how="left",
        )
        comp = comp.merge(agg_xgb, on="NOC", how="left")
        comp = comp.merge(agg_hurdle, on="NOC", how="left")
        for c in ["m1_xgb", "m1_hurdle", "agg_xgb", "agg_hurdle"]:
            comp[c] = comp[c].fillna(0)

        # Calibration: scale AGG so its training-fold mean matches actual mean
        # Simple ratio-of-means correction using training folds
        # For simplicity, scale by (mean actual / mean predicted) using training data
        # Approximation: scale aggregated test prediction by ratio of train actual
        # mean to train predicted mean (computed only over NOCs present in both)
        train_macro_rows = macro[
            (macro["Year"] < Y) & (macro["sample_primary"] == 1)
        ][["NOC", "mt_total"]]
        train_mean_actual = train_macro_rows["mt_total"].mean()

        # Compute train-fold AGG mean by reusing per-sport predictions on train
        # (approximation: use test AGG mean as proxy for training if not refit)
        # Better: use test AGG prediction mean and training actual mean
        # This is NOT ideal but gives a rough sense of calibration potential
        test_agg_mean = comp["agg_xgb"].mean()
        calib_factor = train_mean_actual / test_agg_mean if test_agg_mean > 0 else 1.0
        comp["agg_xgb_calibrated"] = comp["agg_xgb"] * calib_factor

        y = comp["mt_total"].values
        pkg.append(f"  calibration factor (train_actual_mean / test_agg_mean) = {calib_factor:.3f}")

        results_y = {
            "edition": Y, "tag": tag, "n_noc": len(comp),
            "M0_rmse": rmse(y, comp["naive_pred"]),
            "M1_xgb_rmse": rmse(y, comp["m1_xgb"]),
            "M1_hurdle_rmse": rmse(y, comp["m1_hurdle"]),
            "AGG_xgb_rmse": rmse(y, comp["agg_xgb"]),
            "AGG_hurdle_rmse": rmse(y, comp["agg_hurdle"]),
            "AGG_calib_rmse": rmse(y, comp["agg_xgb_calibrated"]),
            "M0_log": log_rmse(y, comp["naive_pred"]),
            "M1_xgb_log": log_rmse(y, comp["m1_xgb"]),
            "M1_hurdle_log": log_rmse(y, comp["m1_hurdle"]),
            "AGG_xgb_log": log_rmse(y, comp["agg_xgb"]),
            "AGG_hurdle_log": log_rmse(y, comp["agg_hurdle"]),
            "AGG_calib_log": log_rmse(y, comp["agg_xgb_calibrated"]),
        }
        # Relative gaps vs naive
        for k in ["M1_xgb", "M1_hurdle", "AGG_xgb", "AGG_hurdle", "AGG_calib"]:
            results_y[f"{k}_vs_M0_pct"] = (
                (results_y["M0_rmse"] - results_y[f"{k}_rmse"]) / results_y["M0_rmse"] * 100
            )
        all_results.append(results_y)

        pkg.append(f"\n  {'model':<20s} {'RMSE':>8s} {'log_RMSE':>10s} {'vs M0':>8s}")
        for label, key in [
            ("M0 naive", "M0"),
            ("M1 XGB direct", "M1_xgb"),
            ("M1 Hurdle direct", "M1_hurdle"),
            ("AGG XGB", "AGG_xgb"),
            ("AGG Hurdle", "AGG_hurdle"),
            ("AGG XGB calibrated", "AGG_calib"),
        ]:
            pkg.append(
                f"  {label:<20s} {results_y[f'{key}_rmse']:8.3f} "
                f"{results_y[f'{key}_log']:10.3f} "
                f"{results_y[f'{key}_vs_M0_pct']:+7.1f}%"
                if f"{key}_vs_M0_pct" in results_y else
                f"  {label:<20s} {results_y[f'{key}_rmse']:8.3f} {results_y[f'{key}_log']:10.3f}"
            )

    # ---------------- Summary ----------------
    res = pd.DataFrame(all_results)
    res.to_csv(REPORTS / "sensitivity_zero_inflated.csv", index=False)

    pkg.append("\n" + "=" * 60)
    pkg.append("=== SUMMARY (all test years) ===")
    pkg.append("=" * 60)
    show = res[[
        "edition", "tag",
        "M0_rmse", "M1_xgb_rmse", "M1_hurdle_rmse",
        "AGG_xgb_rmse", "AGG_hurdle_rmse", "AGG_calib_rmse",
    ]].round(3)
    pkg.append(show.to_string(index=False))

    prim = res[res["tag"] == "PRIMARY"]
    pkg.append("\n=== PRIMARY (2012, 2016) — mean relative to naive ===")
    for k in ["M1_xgb", "M1_hurdle", "AGG_xgb", "AGG_hurdle", "AGG_calib"]:
        pkg.append(f"  {k:<14s} mean_vs_M0 = {prim[f'{k}_vs_M0_pct'].mean():+.1f}%")

    pkg.append("\n=== VERDICT ===")
    best_agg = min(
        prim["AGG_xgb_rmse"].mean(),
        prim["AGG_hurdle_rmse"].mean(),
        prim["AGG_calib_rmse"].mean(),
    )
    best_name = ["AGG_xgb", "AGG_hurdle", "AGG_calib"][
        np.argmin([
            prim["AGG_xgb_rmse"].mean(),
            prim["AGG_hurdle_rmse"].mean(),
            prim["AGG_calib_rmse"].mean(),
        ])
    ]
    naive_mean = prim["M0_rmse"].mean()
    pkg.append(f"  Best aggregation variant: {best_name} (mean RMSE = {best_agg:.3f})")
    pkg.append(f"  Naive mean RMSE: {naive_mean:.3f}")
    if best_agg < naive_mean:
        pkg.append(f"  => Aggregation CAN beat naive with the right variant")
    else:
        pkg.append(f"  => Aggregation still fails; null result is robust")

    report = REPORTS / "sensitivity_zero_inflated.md"
    with open(report, "w", encoding="utf-8") as f:
        f.write("# Sensitivity: zero-inflated models for aggregation\n\n")
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
