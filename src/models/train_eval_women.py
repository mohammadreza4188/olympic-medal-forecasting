"""
train_eval_women.py
===================
Chapter 3.2 forward-chaining evaluation: does gender-specific information
beyond female_share improve prediction?

Variants tested:
- M1: macro baseline (contains female_share, lag_mt_total)
- M1_women: M1 + log_female_athletes + lag_female_medal_share + female_athletes_to_pop_ratio
- M1_women_rca: M1_women + female RCA aggregates (rca_mean_weighted_female, ...)

Forward-chaining on 2012, 2016, 2020, 2024. Four families.
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
DATASET = PROCESSED / "model_dataset_women.csv"

MACRO_BASE = [
    "log_gdp_const_avg4y", "log_gdp_pcap_const_avg4y", "log_population_avg4y",
    "athletes", "sports", "events", "female_share", "host",
    "lag_mt_total", "lag_mt_gold",
]
WOMEN_EXTRA = [
    "log_female_athletes", "lag_female_medal_share",
    "female_athletes_to_pop_ratio",
    "lag_female_medal_share_missing",
]
WOMEN_RCA = [
    "rca_mean_weighted_female", "n_sports_rca_gt1_female",
    "medal_hhi_female",
]

VARIANTS = {
    "M1": MACRO_BASE,
    "M1_women": MACRO_BASE + WOMEN_EXTRA,
    "M1_women_rca": MACRO_BASE + WOMEN_EXTRA + WOMEN_RCA,
}

FAMILIES = ["poisson", "hurdle", "rf", "xgb"]
TEST_YEARS = [2012, 2016, 2020, 2024]


def fit_predict(family, X_tr, y_tr, X_te):
    if family == "poisson":
        m = Pipeline([("scaler", StandardScaler()),
                      ("poisson", PoissonRegressor(alpha=0.1, max_iter=1000))])
        m.fit(X_tr, y_tr)
        return m.predict(X_te)
    if family == "hurdle":
        clf = Pipeline([("scaler", StandardScaler()),
                        ("clf", LogisticRegression(C=1.0, max_iter=1000, random_state=SEED))])
        clf.fit(X_tr, (y_tr > 0).astype(int))
        p_any = clf.predict_proba(X_te)[:, 1]
        pos = y_tr > 0
        if pos.sum() >= 5:
            cnt = Pipeline([("scaler", StandardScaler()),
                            ("poisson", PoissonRegressor(alpha=0.1, max_iter=1000))])
            cnt.fit(X_tr[pos], y_tr[pos])
            mp = cnt.predict(X_te)
        else:
            mp = np.full(len(X_te), float(y_tr[pos].mean()) if pos.any() else 1.0)
        return p_any * mp
    if family == "rf":
        m = RandomForestRegressor(n_estimators=300, max_depth=10, min_samples_leaf=3,
                                  random_state=SEED, n_jobs=-1)
        m.fit(X_tr, y_tr)
        return m.predict(X_te)
    if family == "xgb":
        m = XGBRegressor(n_estimators=400, max_depth=4, learning_rate=0.05,
                         objective="count:poisson", random_state=SEED,
                         verbosity=0, n_jobs=-1)
        m.fit(X_tr, y_tr)
        return m.predict(X_te)
    raise ValueError(family)


def metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.clip(np.asarray(y_pred, dtype=float), 0, None)
    return {
        "rmse": float(np.sqrt(np.mean((y_true - y_pred) ** 2))),
        "log_rmse": float(np.sqrt(np.mean(
            (np.log1p(y_true) - np.log1p(y_pred)) ** 2))),
        "spearman": float(spearmanr(y_true, y_pred).statistic) if len(y_true) > 1 else np.nan,
    }


def main():
    df = pd.read_csv(DATASET, encoding="utf-8-sig", low_memory=False)
    primary = df[df["sample_primary"] == 1].copy()
    pkg = [
        "=== Chapter 3.2: Women's feature evaluation ===",
        f"seed={SEED}",
        f"primary: rows={len(primary)} editions={sorted(primary['Year'].unique().tolist())}",
        f"variants: {list(VARIANTS.keys())}",
    ]

    results = []
    for Y in TEST_YEARS:
        tr = primary[primary["Year"] < Y]
        te = primary[primary["Year"] == Y]
        y_te = te["mt_total"].values
        pkg.append(f"\n--- test {Y}: train={len(tr)} test={len(te)}")

        # M0 naive
        y0 = te["lag_mt_total"].values.astype(float)
        m0 = metrics(y_te, y0)
        results.append({"edition": Y, "variant": "M0", "family": "naive", **m0})
        pkg.append(f"  M0        /naive    rmse={m0['rmse']:7.3f}  log_rmse={m0['log_rmse']:.3f}  rho={m0['spearman']:.3f}")

        for vname, feats in VARIANTS.items():
            trv = tr.dropna(subset=feats)
            if len(trv) < 20:
                pkg.append(f"  {vname}: insufficient rows")
                continue
            X_tr = trv[feats].values
            y_tr = trv["mt_total"].values
            X_te = te[feats].values
            for fam in FAMILIES:
                try:
                    pred = fit_predict(fam, X_tr, y_tr, X_te)
                except Exception as e:
                    pkg.append(f"  {vname}/{fam}: ERROR {e}")
                    continue
                m = metrics(y_te, pred)
                results.append({"edition": Y, "variant": vname, "family": fam, **m})
                pkg.append(
                    f"  {vname:<12s}/{fam:<7s} rmse={m['rmse']:7.3f}  "
                    f"log_rmse={m['log_rmse']:.3f}  rho={m['spearman']:.3f}"
                )

    res = pd.DataFrame(results)
    res.to_csv(REPORTS / "phase7a_women_results.csv", index=False)

    pkg.append("\n=== Aggregate ===")
    agg = res.groupby(["variant", "family"]).agg(
        rmse_mean=("rmse", "mean"),
        log_rmse_mean=("log_rmse", "mean"),
        rho_mean=("spearman", "mean"),
    ).round(3).reset_index()
    pkg.append(agg.to_string(index=False))

    pkg.append("\n=== M1_women vs M1 ===")
    pv = res.pivot_table(index=["edition", "family"], columns="variant", values="rmse").reset_index()
    pv["women_vs_M1_pct"] = (pv["M1"] - pv["M1_women"]) / pv["M1"] * 100
    pv["women_rca_vs_M1_pct"] = (pv["M1"] - pv["M1_women_rca"]) / pv["M1"] * 100
    pkg.append(pv.round(3).to_string(index=False))

    fam = pv.groupby("family").agg(
        women_mean=("women_vs_M1_pct", "mean"),
        women_min=("women_vs_M1_pct", "min"),
        women_max=("women_vs_M1_pct", "max"),
        n_pos=("women_vs_M1_pct", lambda s: int((s > 0).sum())),
        women_rca_mean=("women_rca_vs_M1_pct", "mean"),
    ).round(3).reset_index()
    pkg.append("\n=== Per-family summary ===")
    pkg.append(fam.to_string(index=False))

    report = REPORTS / "phase7a_women_results.md"
    with open(report, "w", encoding="utf-8") as f:
        f.write("# Chapter 3.2 — Women's feature evaluation\n\n")
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
