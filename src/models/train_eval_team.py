"""
train_eval_team.py
==================
Chapter 3.4 evaluation: team vs individual medal prediction.

Two targets, same macro feature block (except lag), four families.
Team target tested on 2012, 2016 only (2020/2024 contaminated — see protocol).
Individual target tested on all four.

See references/ch04_team_protocol.md.
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

FAMILIES = ["poisson", "hurdle", "rf", "xgb"]

# Team target contaminated in 2020/2024 (74 missing events per edition are
# predominantly team events). Individual target is stable. See protocol.
TEST_YEARS_PER_TARGET = {
    "team_medals":       [2012, 2016],
    "individual_medals": [2012, 2016, 2020, 2024],
}


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
        "=== Chapter 3.4: team vs individual evaluation ===",
        f"seed={SEED}",
        f"primary: rows={len(primary)} editions={sorted(primary['Year'].unique().tolist())}",
    ]

    results = []
    for target, variants in VARIANTS.items():
        test_years = TEST_YEARS_PER_TARGET[target]
        pkg.append(f"\n########## TARGET = {target} ##########")
        pkg.append(f"test years for this target: {test_years}")

        for Y in test_years:
            tr = primary[primary["Year"] < Y]
            te = primary[primary["Year"] == Y]
            y_te = te[target].values

            # M0 naive
            m0 = metrics(y_te, te[f"lag_{target}"].values.astype(float))
            results.append({"target": target, "edition": Y,
                            "variant": "M0", "family": "naive", **m0})
            pkg.append(f"\n--- {Y}: train={len(tr)} test={len(te)}  "
                       f"zero_share={float((y_te == 0).mean()):.3f}")
            pkg.append(f"  M0/naive    rmse={m0['rmse']:7.3f}  log_rmse={m0['log_rmse']:.3f}  rho={m0['spearman']:.3f}")

            for vname, feats in variants.items():
                trv = tr.dropna(subset=feats)
                if len(trv) < 20:
                    continue
                X_tr = trv[feats].values
                y_tr = trv[target].values
                X_te = te[feats].values
                for fam in FAMILIES:
                    try:
                        pred = fit_predict(fam, X_tr, y_tr, X_te)
                    except Exception as e:
                        pkg.append(f"  {vname}/{fam}: ERROR {e}")
                        continue
                    m = metrics(y_te, pred)
                    results.append({"target": target, "edition": Y,
                                    "variant": vname, "family": fam, **m})
                    pkg.append(
                        f"  {vname:<9s}/{fam:<7s}  rmse={m['rmse']:7.3f}  "
                        f"log_rmse={m['log_rmse']:.3f}  rho={m['spearman']:.3f}"
                    )

    res = pd.DataFrame(results)
    res.to_csv(REPORTS / "phase7b_team_results.csv", index=False)

    pkg.append("\n=== Aggregate by (target, variant, family) ===")
    agg = res.groupby(["target", "variant", "family"]).agg(
        rmse_mean=("rmse", "mean"),
        log_rmse_mean=("log_rmse", "mean"),
        rho_mean=("spearman", "mean"),
        n_editions=("rmse", "count"),
    ).round(3).reset_index()
    pkg.append(agg.to_string(index=False))

    pkg.append("\n=== H3b: relative RMSE improvement over naive, per target ===")
    pivot = res.pivot_table(
        index=["target", "edition", "family"], columns="variant", values="rmse"
    ).reset_index()
    for target in VARIANTS.keys():
        sub = pivot[pivot["target"] == target].copy()
        if "M0" not in sub.columns:
            continue
        sub["M1_gap"] = (sub["M0"] - sub["M1"]) / sub["M0"] * 100
        sub["M1_noLag_gap"] = (sub["M0"] - sub["M1_noLag"]) / sub["M0"] * 100
        pkg.append(f"\n--- {target} ---")
        for fam in FAMILIES:
            f_sub = sub[sub["family"] == fam]
            if len(f_sub) == 0:
                continue
            pkg.append(
                f"  {fam:<7s}  M1_gap_mean={f_sub['M1_gap'].mean():+6.1f}%   "
                f"M1_noLag_gap_mean={f_sub['M1_noLag_gap'].mean():+6.1f}%"
            )

    report = REPORTS / "phase7b_team_results.md"
    with open(report, "w", encoding="utf-8") as f:
        f.write("# Chapter 3.4 — Team vs individual evaluation\n\n")
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
