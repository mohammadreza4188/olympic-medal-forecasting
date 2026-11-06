"""
build_discipline_features.py
============================
Build country-by-sport specialization features (Balassa RCA) from athlete_events
and aggregate them to country-edition rows.

Usage (from project root):
    python src/build/build_discipline_features.py

See references/discipline_features_protocol.md for methodology.
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

AE_PATH = RAW / "athlete_events_through_2026.csv"
PANEL_IN = PROCESSED / "panel_summer_macro_v2.csv"
OUT_FEATURES = PROCESSED / "discipline_features.csv"
OUT_SPORT = PROCESSED / "discipline_sport_medals.csv"

VARIANTS = ["total", "gold", "female", "male"]
WINDOWS = ["cum", "last4"]


# ---------------------------------------------------------------- helpers

def build_medals_long(ae):
    """Return long dataframe: (NOC, Year, Sport, Medal, Sex) -> one row per medal."""
    ae = ae[ae["Season"] == "Summer"].copy()
    ae = ae[ae["Medal"].notna()].copy()
    # Team-medal de-dup: one medal per (NOC, Year, Event, Medal).
    ae = ae.drop_duplicates(subset=["NOC", "Year", "Sport", "Event", "Medal"])
    out = ae[["NOC", "Year", "Sport", "Medal", "Sex"]].copy()
    out["Year"] = out["Year"].astype(int)
    return out


def filter_variant(medals_long, variant):
    if variant == "total":
        return medals_long
    if variant == "gold":
        return medals_long[medals_long["Medal"] == "Gold"]
    if variant == "female":
        return medals_long[medals_long["Sex"] == "F"]
    if variant == "male":
        return medals_long[medals_long["Sex"] == "M"]
    raise ValueError(variant)


def compute_rca(noc_sport_counts, target_years):
    """
    noc_sport_counts: df with columns NOC, Sport, Year (one row per medal).
    For each target year Y in target_years, use editions with Year < Y
    (window is set upstream).
    Returns df: (NOC, Sport, Year, medals, rca).
    """
    rows = []
    for Y in target_years:
        sub = noc_sport_counts[noc_sport_counts["Year"] < Y]
        if len(sub) == 0:
            continue
        m_cs = sub.groupby(["NOC", "Sport"]).size().rename("medals").reset_index()
        m_c = m_cs.groupby("NOC")["medals"].sum().rename("m_country").reset_index()
        m_s = m_cs.groupby("Sport")["medals"].sum().rename("m_sport").reset_index()
        m_tot = int(m_cs["medals"].sum())
        if m_tot == 0:
            continue
        merged = m_cs.merge(m_c, on="NOC").merge(m_s, on="Sport")
        merged["rca"] = (
            (merged["medals"] / merged["m_country"])
            / (merged["m_sport"] / m_tot)
        )
        merged["Year"] = Y
        rows.append(merged[["NOC", "Sport", "Year", "medals", "rca"]])
    if not rows:
        return pd.DataFrame(columns=["NOC", "Sport", "Year", "medals", "rca"])
    return pd.concat(rows, ignore_index=True)


def aggregate_features(sport_rca):
    """Reduce (NOC, Sport, Year, medals, rca) to one row per (NOC, Year)."""
    if len(sport_rca) == 0:
        return pd.DataFrame(columns=[
            "NOC", "Year",
            "rca_mean_weighted", "rca_max", "rca_p75",
            "n_sports_rca_gt1", "n_sports_rca_gt1p5",
            "medal_hhi", "n_sports_medal", "medal_share_top_sport",
        ])

    def agg(g):
        w = g["medals"].to_numpy(dtype=float)
        r = g["rca"].to_numpy(dtype=float)
        total = w.sum()
        if total <= 0 or not np.isfinite(r).any():
            return pd.Series({
                "rca_mean_weighted": np.nan,
                "rca_max": np.nan,
                "rca_p75": np.nan,
                "n_sports_rca_gt1": 0,
                "n_sports_rca_gt1p5": 0,
                "medal_hhi": np.nan,
                "n_sports_medal": 0,
                "medal_share_top_sport": np.nan,
            })
        shares = w / total
        return pd.Series({
            "rca_mean_weighted": float((r * w).sum() / total),
            "rca_max": float(np.nanmax(r)),
            "rca_p75": float(np.nanpercentile(r, 75)),
            "n_sports_rca_gt1": int((r > 1.0).sum()),
            "n_sports_rca_gt1p5": int((r > 1.5).sum()),
            "medal_hhi": float((shares ** 2).sum()),
            "n_sports_medal": int(len(g)),
            "medal_share_top_sport": float(shares.max()),
        })

    out = (
        sport_rca
        .groupby(["NOC", "Year"])
        .apply(agg, include_groups=False)
        .reset_index()
    )
    return out


def build_variant_window(medals_long, variant, window, target_years, all_years_sorted):
    sub = filter_variant(medals_long, variant)
    if len(sub) == 0:
        return pd.DataFrame()

    if window == "cum":
        sport_rca = compute_rca(sub, target_years)
    elif window == "last4":
        frames = []
        for Y in target_years:
            prior = [y for y in all_years_sorted if y < Y]
            keep = set(prior[-4:]) if prior else set()
            s = sub[sub["Year"].isin(keep)].copy()
            if len(s) == 0:
                continue
            # Reuse compute_rca on the filtered window by pretending "Year < Y+1"
            m_cs = s.groupby(["NOC", "Sport"]).size().rename("medals").reset_index()
            m_c = m_cs.groupby("NOC")["medals"].sum().rename("m_country").reset_index()
            m_s = m_cs.groupby("Sport")["medals"].sum().rename("m_sport").reset_index()
            m_tot = int(m_cs["medals"].sum())
            if m_tot == 0:
                continue
            merged = m_cs.merge(m_c, on="NOC").merge(m_s, on="Sport")
            merged["rca"] = (
                (merged["medals"] / merged["m_country"])
                / (merged["m_sport"] / m_tot)
            )
            merged["Year"] = Y
            frames.append(merged[["NOC", "Sport", "Year", "medals", "rca"]])
        sport_rca = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(
            columns=["NOC", "Sport", "Year", "medals", "rca"]
        )
    else:
        raise ValueError(window)

    if len(sport_rca) == 0:
        return pd.DataFrame()

    features = aggregate_features(sport_rca)
    features["variant"] = variant
    features["window"] = window
    sport_rca["variant"] = variant
    sport_rca["window"] = window
    return features, sport_rca


# ---------------------------------------------------------------- main

def main():
    pkg = []

    panel = pd.read_csv(PANEL_IN, encoding="utf-8-sig", low_memory=False)
    target_years = sorted(panel["Year"].dropna().astype(int).unique().tolist())
    pkg.append(f"panel v2: shape={panel.shape}  target_years n={len(target_years)}")

    ae = pd.read_csv(AE_PATH, encoding="utf-8", low_memory=False)
    pkg.append(f"athlete_events: shape={ae.shape}")

    medals_long = build_medals_long(ae)
    pkg.append(f"medals_long (Summer, de-duped): shape={medals_long.shape}")
    all_years_sorted = sorted(medals_long["Year"].unique().tolist())
    pkg.append(f"edition years in medals_long: {all_years_sorted[:5]} ... {all_years_sorted[-5:]}")

    all_features = []
    all_sport_rca = []
    for variant in VARIANTS:
        for window in WINDOWS:
            res = build_variant_window(
                medals_long, variant, window, target_years, all_years_sorted
            )
            if isinstance(res, pd.DataFrame):
                if len(res) == 0:
                    pkg.append(f"  {variant}/{window}: EMPTY")
                    continue
            else:
                features, sport_rca = res
                all_features.append(features)
                all_sport_rca.append(sport_rca)
                pkg.append(f"  {variant}/{window}: features={len(features)} sport_rows={len(sport_rca)}")

    if not all_features:
        pkg.append("ERROR: no features produced. Check source data.")
        _dump(pkg, None, None)
        return

    features = pd.concat(all_features, ignore_index=True)
    sport_rca = pd.concat(all_sport_rca, ignore_index=True)

    # Sanity checks
    assert features.duplicated(subset=["NOC", "Year", "variant", "window"]).sum() == 0, \
        "duplicate feature rows"
    assert (features["Year"] >= panel["Year"].min()).all(), "target year out of range"

    features.to_csv(OUT_FEATURES, index=False, encoding="utf-8-sig")
    sport_rca.to_csv(OUT_SPORT, index=False, encoding="utf-8-sig")

    pkg.append(f"\nfeatures saved: shape={features.shape}")
    pkg.append(f"sport_rca saved: shape={sport_rca.shape}")

    pkg.append("\nfeature columns: " + str(list(features.columns)))

    pkg.append("\ncoverage per variant/window (share of (NOC,Year) rows with rca_mean_weighted not NaN):")
    for v in VARIANTS:
        for w in WINDOWS:
            sub = features[(features["variant"] == v) & (features["window"] == w)]
            if len(sub) == 0:
                continue
            share = sub["rca_mean_weighted"].notna().mean()
            pkg.append(f"  {v:<7s} {w:<6s}  rows={len(sub):>5d}  rca_cov={share:.2f}")

    pkg.append("\nkey-year coverage (variant=total, window=last4):")
    sub = features[(features["variant"] == "total") & (features["window"] == "last4")]
    for y in [1980, 2000, 2008, 2016, 2020, 2024]:
        s = sub[sub["Year"] == y]
        if len(s) == 0:
            continue
        pkg.append(f"  {y}: n={len(s):>3d}  rca_cov={s['rca_mean_weighted'].notna().mean():.2f}")

    pkg.append("\ntop-specialized-sport examples (variant=total, window=last4, target 2024):")
    ex = sport_rca[
        (sport_rca["variant"] == "total")
        & (sport_rca["window"] == "last4")
        & (sport_rca["Year"] == 2024)
    ]
    for noc in ["USA", "CHN", "KEN", "HUN", "JAM", "GBR"]:
        row = (
            ex[ex["NOC"] == noc]
            .sort_values("rca", ascending=False)
            .head(2)
            [["Sport", "medals", "rca"]]
        )
        if len(row) == 0:
            continue
        parts = [f"{r.Sport} (m={int(r.medals)}, rca={r.rca:.2f})" for r in row.itertuples()]
        pkg.append(f"  {noc}: " + " | ".join(parts))

    pkg.append("\nsample feature rows (target 2024, variant=total):")
    s = features[
        (features["Year"] == 2024) & (features["variant"] == "total")
    ][[
        "NOC", "window",
        "rca_mean_weighted", "rca_max", "rca_p75",
        "n_sports_rca_gt1", "medal_hhi", "n_sports_medal",
    ]].sort_values(["NOC", "window"]).head(12)
    pkg.append(s.to_string(index=False))

    _dump(pkg, features, sport_rca)


def _dump(pkg, features, sport_rca):
    report_path = REPORTS / "phase4b_discipline_features.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Discipline features + Balassa RCA — Phase 4b\n\n")
        f.write("Generated by `src/build/build_discipline_features.py`.\n\n")
        f.write("See `references/discipline_features_protocol.md` for methodology.\n\n")
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
