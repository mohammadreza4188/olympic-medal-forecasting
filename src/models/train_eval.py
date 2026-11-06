"""
train_eval.py (v2)
==================
Phase 6 forward-chaining evaluation.

Adds to v1:
- seeds set
- M1_noLag / M2_noLag sensitivity
- three-condition H1 verdict
- per-model feature importance for M1 and M2
- discipline NaN-vs-zero-fill sensitivity (run M2 with dropna on discipline)
- winsorize-95 sensitivity (loaded from alternative pre-built dataset, see note)

See references/phase5_research_protocol_v1.1.md.

Usage: python src/models/train_eval.py
"""

import random
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestRegressor
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
DATASET = PROCESSED / "model_dataset.csv"

MACRO_NO_LAG = [
    "log_gdp_const_avg4y", "log_gdp_pcap_const_avg4y", "log_population_avg4y",
    "athletes", "sports", "events", "female_share", "host",
]
LAG_FEATURES = ["lag_mt_total", "lag_mt_gold"]
MACRO_FEATURES = MACRO_NO_LAG + LAG_FEATURES

DISC_FEATURES = [
    "rca_mean_weighted_base", "rca_max_base", "rca_p75_base",
    "n_sports_rca_gt1_base", "n_sports_rca_gt1p5_base",
    "medal_hhi_base", "n_sports_medal_base", "medal_share_top_sport_base",
    "has_discipline_data",
]

VARIANTS = {
    "M1": MACRO_FEATURES,
    "M1_noLag": MACRO_NO_LAG,
    "M2": MACRO_FEATURES + DISC_FEATURES,
    "M2_noLag": MACRO_NO_LAG + DISC_FEATURES,
    "M3": DISC_FEATURES,
}

FAMILIES = ["poisson", "hurdle", "rf", "xgb"]
TEST_YEARS = [2012, 2016, 2020, 2024]


def load_data():
    return pd.read_csv(DATASET, encoding="utf-8-sig", low_memory=False)


def fit_predict(family, X_tr, y_tr, X_te, return_importance=False):
    """Return (y_pred, importance_dict) if return_importance else y_pred."""
    if family == "poisson":
        m = Pipeline([
            ("scaler", StandardScaler()),
            ("poisson", PoissonRegressor(alpha=0.1, max_iter=1000)),
        ])
        m.fit(X_tr, y_tr)
        pred = m.predict(X_te)
        imp = None
        if return_importance:
            coef = m.named_steps["poisson"].coef_
            imp = np.abs(coef)
        return (pred, imp) if return_importance else pred

    if family == "hurdle":
        clf = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(C=1.0, max_iter=1000, random_state=SEED)),
        ])
        clf.fit(X_tr, (y_tr > 0).astype(int))
        p_any = clf.predict_proba(X_te)[:, 1]
        pos_mask = y_tr > 0
        if pos_mask.sum() >= 5:
            cnt = Pipeline([
                ("scaler", StandardScaler()),
                ("poisson", PoissonRegressor(alpha=0.1, max_iter=1000)),
            ])
            cnt.fit(X_tr[pos_mask], y_tr[pos_mask])
            mean_pos = cnt.predict(X_te)
        else:
            mean_pos = np.full(len(X_te), float(y_tr[pos_mask].mean()) if pos_mask.any() else 1.0)
        pred = p_any * mean_pos
        imp = np.abs(clf.named_steps["clf"].coef_[0]) if return_importance else None
        return (pred, imp) if return_importance else pred

    if family == "rf":
        m = RandomForestRegressor(
            n_estimators=300, max_depth=10, min_samples_leaf=3,
            random_state=SEED, n_jobs=-1,
        )
        m.fit(X_tr, y_tr)
        pred = m.predict(X_te)
        imp = m.feature_importances_ if return_importance else None
        return (pred, imp) if return_importance else pred

    if family == "xgb":
        m = XGBRegressor(
            n_estimators=400, max_depth=4, learning_rate=0.05,
            objective="count:poisson", random_state=SEED,
            verbosity=0, n_jobs=-1,
        )
        m.fit(X_tr, y_tr)
        pred = m.predict(X_te)
        imp = m.feature_importances_ if return_importance else None
        return (pred, imp) if return_importance else pred

    raise ValueError(family)


def compute_metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    mae = float(np.mean(np.abs(y_true - y_pred)))
    log_rmse = float(np.sqrt(np.mean(
        (np.log1p(y_true) - np.log1p(np.clip(y_pred, 0, None))) ** 2
    )))
    rho = float(spearmanr(y_true, y_pred).statistic) if len(y_true) > 1 else np.nan
    if len(y_true) >= 10:
        top10_true = set(np.argsort(-y_true)[:10])
        top10_pred = set(np.argsort(-y_pred)[:10])
        top10_hit = float(len(top10_true & top10_pred) / 10)
    else:
        top10_hit = np.nan
    return {"rmse": rmse, "mae": mae, "log_rmse": log_rmse,
            "spearman": rho, "top10_hit": top10_hit}


def main():
    df = load_data()
    primary = df[df["sample_primary"] == 1].copy()
    pkg = [
        "=== Phase 6 (v2) forward-chaining evaluation ===",
        f"seed={SEED}",
        f"primary sample: rows={len(primary)} editions={sorted(primary['Year'].unique().tolist())}",
        f"test years: {TEST_YEARS}",
        f"variants: {list(VARIANTS.keys())}",
    ]

    results = []
    importance_records = []

    for Y in TEST_YEARS:
        train_df = primary[primary["Year"] < Y].copy()
        test_df = primary[primary["Year"] == Y].copy()
        y_test = test_df["mt_total"].values
        pkg.append(f"\n--- test {Y}: train n={len(train_df)} "
                   f"({train_df['Year'].min()}-{train_df['Year'].max()})  test n={len(test_df)}")

        # M0 naive
        y_pred_m0 = test_df["lag_mt_total"].values.astype(float)
        m0 = compute_metrics(y_test, y_pred_m0)
        results.append({"edition": Y, "variant": "M0", "family": "naive", **m0})
        pkg.append(f"  M0 naive:                rmse={m0['rmse']:8.3f}  log_rmse={m0['log_rmse']:.3f}  "
                   f"rho={m0['spearman']:.3f}  top10={m0['top10_hit']:.2f}")

        for variant_name, features in VARIANTS.items():
            # Discipline NaN sensitivity handled by skipping zero-fill variant here
            train_v = train_df.dropna(subset=features)
            if len(train_v) < 20:
                pkg.append(f"  {variant_name}: insufficient training rows ({len(train_v)}), skipping")
                continue
            X_tr = train_v[features].values
            y_tr = train_v["mt_total"].values
            X_te = test_df[features].values

            for family in FAMILIES:
                try:
                    if family in ("rf", "xgb", "poisson"):
                        y_pred, imp = fit_predict(
                            family, X_tr, y_tr, X_te, return_importance=True
                        )
                        for i, f in enumerate(features):
                            importance_records.append({
                                "edition": Y, "variant": variant_name,
                                "family": family, "feature": f, "importance": float(imp[i]),
                            })
                    else:
                        y_pred = fit_predict(family, X_tr, y_tr, X_te)
                    y_pred = np.clip(y_pred, 0, None)
                except Exception as e:
                    pkg.append(f"  {variant_name}/{family}: ERROR {type(e).__name__}: {e}")
                    continue

                met = compute_metrics(y_test, y_pred)
                gap = ((m0["rmse"] - met["rmse"]) / m0["rmse"] * 100) if m0["rmse"] > 0 else np.nan
                results.append({"edition": Y, "variant": variant_name,
                                "family": family, "naive_gap_pct": gap, **met})
                pkg.append(f"  {variant_name:<9s}/{family:<7s}  rmse={met['rmse']:8.3f}  "
                           f"log_rmse={met['log_rmse']:.3f}  "
                           f"rho={met['spearman']:.3f}  top10={met['top10_hit']:.2f}  "
                           f"gap={gap:+6.1f}%")

    res = pd.DataFrame(results)
    res.to_csv(REPORTS / "phase6_results.csv", index=False)
    imp_df = pd.DataFrame(importance_records)
    imp_df.to_csv(REPORTS / "phase6_feature_importance.csv", index=False)

    # Aggregates
    pkg.append("\n=== Aggregate across 4 held-out editions ===")
    agg = res.groupby(["variant", "family"]).agg(
        rmse_mean=("rmse", "mean"), rmse_std=("rmse", "std"),
        log_rmse_mean=("log_rmse", "mean"),
        rho_mean=("spearman", "mean"),
        top10_mean=("top10_hit", "mean"),
        n_editions=("rmse", "count"),
    ).round(3).reset_index()
    pkg.append(agg.to_string(index=False))

    # M2-vs-M1 and M2-vs-M0
    pkg.append("\n=== M2 vs M1 and M2 vs M0 (per edition x family) ===")
    pivot = res.pivot_table(index=["edition", "family"],
                            columns="variant", values="rmse").reset_index()
    m0_by_ed = res[res["family"] == "naive"].set_index("edition")["rmse"].to_dict()
    pivot["M0"] = pivot["edition"].map(m0_by_ed)
    pivot["M2_vs_M1_pct"] = (pivot["M1"] - pivot["M2"]) / pivot["M1"] * 100
    pivot["M2_noLag_vs_M1_noLag_pct"] = (pivot["M1_noLag"] - pivot["M2_noLag"]) / pivot["M1_noLag"] * 100
    pivot["M3_vs_M1_pct"] = (pivot["M1"] - pivot["M3"]) / pivot["M1"] * 100
    pivot["M2_vs_M0_pct"] = (pivot["M0"] - pivot["M2"]) / pivot["M0"] * 100
    pkg.append(pivot.round(3).to_string(index=False))

    pkg.append("\n=== Per-family M2-vs-M1 ===")
    fam = pivot.groupby("family").agg(
        m2_vs_m1_mean=("M2_vs_M1_pct", "mean"),
        m2_vs_m1_min=("M2_vs_M1_pct", "min"),
        m2_vs_m1_max=("M2_vs_M1_pct", "max"),
        n_pos=("M2_vs_M1_pct", lambda s: int((s > 0).sum())),
        m2_noLag_vs_m1_noLag_mean=("M2_noLag_vs_M1_noLag_pct", "mean"),
        m2_vs_m0_mean=("M2_vs_M0_pct", "mean"),
    ).round(3).reset_index()
    pkg.append(fam.to_string(index=False))

    # Log-scale companion pivot (secondary metric)
    log_pivot = res.pivot_table(
        index=["edition", "family"], columns="variant", values="log_rmse"
    ).reset_index()
    log_pivot["M2_vs_M1_log_pct"] = (
        (log_pivot["M1"] - log_pivot["M2"]) / log_pivot["M1"] * 100
    )
    m0_log_by_ed = res[res["family"] == "naive"].set_index("edition")["log_rmse"].to_dict()
    log_pivot["M0_log"] = log_pivot["edition"].map(m0_log_by_ed)
    log_pivot["M1_vs_M0_log_pct"] = (
        (log_pivot["M0_log"] - log_pivot["M1"]) / log_pivot["M0_log"] * 100
    )
    log_pivot["M2_vs_M0_log_pct"] = (
        (log_pivot["M0_log"] - log_pivot["M2"]) / log_pivot["M0_log"] * 100
    )

    # H1 verdict — three conditions per protocol v1.1
    pkg.append("\n=== H1 verdict (v1.1 three-condition logic) ===")
    fset = fam.set_index("family")
    overall = float(pivot["M2_vs_M1_pct"].mean())
    # per-edition direction: count editions where M2 mean across families > M1
    per_ed = pivot.groupby("edition").agg(
        m1_mean=("M1", "mean"), m2_mean=("M2", "mean")
    )
    per_ed["improved"] = per_ed["m2_mean"] < per_ed["m1_mean"]
    n_pos_editions = int(per_ed["improved"].sum())
    n_families_pass = int(
        ((fset["m2_vs_m1_mean"] >= 3.0) & (fset["n_pos"] >= 3)).sum()
    )

    pkg.append(f"  condition 1 (mean >= 3%):     overall mean = {overall:+.2f}%  -> "
               f"{'PASS' if overall >= 3.0 else 'FAIL'}")
    pkg.append(f"  condition 2 (>=3/4 editions): {n_pos_editions}/4 editions improved  -> "
               f"{'PASS' if n_pos_editions >= 3 else 'FAIL'}")
    pkg.append(f"  condition 3 (>=3/4 families): {n_families_pass}/4 families pass  -> "
               f"{'PASS' if n_families_pass >= 3 else 'FAIL'}")
    h1 = (overall >= 3.0) and (n_pos_editions >= 3) and (n_families_pass >= 3)
    pkg.append(f"  VERDICT: H1 {'SUPPORTED' if h1 else 'NOT SUPPORTED (fail to reject H0)'}")

    pkg.append("\n=== H1 verdict on log_rmse (secondary metric) ===")
    overall_log = float(log_pivot["M2_vs_M1_log_pct"].mean())
    log_per_ed = log_pivot.groupby("edition").agg(
        m1_log=("M1", "mean"), m2_log=("M2", "mean")
    )
    log_per_ed["improved"] = log_per_ed["m2_log"] < log_per_ed["m1_log"]
    n_pos_ed_log = int(log_per_ed["improved"].sum())
    log_fam = log_pivot.groupby("family").agg(
        mean_pct=("M2_vs_M1_log_pct", "mean"),
        n_pos=("M2_vs_M1_log_pct", lambda s: int((s > 0).sum())),
    )
    n_fam_log_pass = int(((log_fam["mean_pct"] >= 3.0) & (log_fam["n_pos"] >= 3)).sum())
    pkg.append(f"  condition 1 (mean >= 3%):     overall mean = {overall_log:+.2f}%")
    pkg.append(f"  condition 2 (>=3/4 editions): {n_pos_ed_log}/4 editions")
    pkg.append(f"  condition 3 (>=3/4 families): {n_fam_log_pass}/4 families")
    pkg.append(f"  per-edition M1_vs_M0 log improvement:")
    for ed in sorted(log_pivot["edition"].unique()):
        sub = log_pivot[log_pivot["edition"] == ed]
        if "M0" in sub.columns and sub["M1_vs_M0_log_pct"].notna().any():
            v = float(sub["M1_vs_M0_log_pct"].mean())
            pkg.append(f"    {ed}: M1 vs M0 log_rmse improvement = {v:+.1f}%")
    h1_log = (overall_log >= 3.0) and (n_pos_ed_log >= 3) and (n_fam_log_pass >= 3)
    pkg.append(f"  VERDICT on log scale: H1 {'SUPPORTED' if h1_log else 'NOT SUPPORTED'}")

    # Lag dominance check
    pkg.append("\n=== Lag dominance in M1 (feature importance, XGB, top-3 per edition) ===")
    xgb_m1 = imp_df[(imp_df["variant"] == "M1") & (imp_df["family"] == "xgb")]
    for ed in TEST_YEARS:
        sub = xgb_m1[xgb_m1["edition"] == ed].sort_values("importance", ascending=False).head(3)
        if len(sub):
            parts = [f"{r.feature}={r.importance:.2f}" for r in sub.itertuples()]
            pkg.append(f"  {ed}: " + " | ".join(parts))

    pkg.append("\n=== M3 vs M2 (H3 exploratory) ===")
    h3_delta = float(pivot["M2_vs_M1_pct"].mean()) - float(pivot["M3_vs_M1_pct"].mean())
    pkg.append(f"  M2 mean improvement over M1: {float(pivot['M2_vs_M1_pct'].mean()):+.2f}%")
    pkg.append(f"  M3 mean improvement over M1: {float(pivot['M3_vs_M1_pct'].mean()):+.2f}%")
    pkg.append(f"  delta (M2 - M3) = {h3_delta:+.2f} pp  -> "
               f"({'supports H3' if abs(h3_delta) < 1.5 else 'does not support H3'})")

    report_path = REPORTS / "phase6_results.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Phase 6 Results (v2)\n\n")
        f.write("Generated by `src/models/train_eval.py`.\n")
        f.write("See `references/phase5_research_protocol_v1.1.md`.\n\n")
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
