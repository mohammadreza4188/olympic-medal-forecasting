"""
build_team_individual.py
========================
Build team_medals and individual_medals targets for Chapter 3.4.

Classification is data-driven: team_size = number of unique athlete IDs per
(NOC, Year, Sport, Event, Medal) tuple.

Adds to model_dataset_women.csv:
- team_medals, individual_medals (current edition, for targets only)
- team_events, ind_events (for descriptive tables only)
- team_athletes, ind_athletes (for descriptive tables only)
- lag_team_medals, lag_individual_medals (features)
- team_share (descriptive)

See references/ch04_team_protocol.md.
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

AE_PATH = RAW / "athlete_events_through_2026.csv"
DATASET_IN = PROCESSED / "model_dataset_women.csv"
DATASET_OUT = PROCESSED / "model_dataset_team.csv"

# Descriptive only — not used for classification
TEAM_SPORTS = {
    "Basketball", "Beach Volleyball", "Football", "Handball", "Hockey",
    "Volleyball", "Water Polo", "Baseball", "Softball", "Rugby Sevens",
    "Rugby", "Polo", "Lacrosse", "Cricket", "Tug-Of-War",
}
INDIVIDUAL_SPORTS = {
    "Athletics", "Swimming", "Gymnastics", "Weightlifting", "Wrestling",
    "Boxing", "Fencing", "Judo", "Taekwondo", "Archery", "Shooting",
    "Cycling", "Equestrianism", "Sailing", "Canoeing", "Rowing",
    "Tennis", "Badminton", "Table Tennis", "Golf", "Triathlon",
    "Modern Pentathlon", "Ski Jumping", "Alpine Skiing", "Biathlon",
    "Bobsleigh", "Luge", "Skeleton", "Figure Skating", "Speed Skating",
    "Short Track Speed Skating", "Nordic Combined", "Freestyle Skiing",
    "Snowboarding", "Curling", "Ice Hockey",
}


def build_targets(ae):
    """Return df with team_medals, individual_medals per (NOC, Year)."""
    sub = ae[(ae["Season"] == "Summer") & (ae["Medal"].notna())].copy()

    # Team size per unique medal
    medal_groups = (
        sub.groupby(["NOC", "Year", "Sport", "Event", "Medal"])
        .agg(team_size=("ID", "nunique"),
             team_athletes=("ID", "nunique"))
        .reset_index()
    )
    medal_groups["is_team"] = (medal_groups["team_size"] > 1).astype(int)

    # Aggregate medals
    agg = medal_groups.groupby(["NOC", "Year"]).agg(
        team_medals=("is_team", "sum"),
        total_medals_from_ae=("is_team", "size"),
    ).reset_index()
    agg["individual_medals"] = agg["total_medals_from_ae"] - agg["team_medals"]

    # team_events: number of distinct events with a team medal
    team_only = medal_groups[medal_groups["is_team"] == 1]
    team_events = team_only.groupby(["NOC", "Year"])["Event"].nunique().rename("team_events").reset_index()

    ind_only = medal_groups[medal_groups["is_team"] == 0]
    ind_events = ind_only.groupby(["NOC", "Year"])["Event"].nunique().rename("ind_events").reset_index()

    team_sports = team_only.groupby(["NOC", "Year"])["Sport"].nunique().rename("team_sports").reset_index()
    ind_sports = ind_only.groupby(["NOC", "Year"])["Sport"].nunique().rename("ind_sports").reset_index()

    agg = agg.merge(team_events, on=["NOC", "Year"], how="left") \
             .merge(ind_events, on=["NOC", "Year"], how="left") \
             .merge(team_sports, on=["NOC", "Year"], how="left") \
             .merge(ind_sports, on=["NOC", "Year"], how="left")

    agg["team_events"] = agg["team_events"].fillna(0).astype(int)
    agg["ind_events"] = agg["ind_events"].fillna(0).astype(int)
    agg["team_sports"] = agg["team_sports"].fillna(0).astype(int)
    agg["ind_sports"] = agg["ind_sports"].fillna(0).astype(int)

    return agg


def gini(x):
    x = np.asarray(x, dtype=float)
    if x.sum() == 0:
        return np.nan
    n = len(x)
    x_sorted = np.sort(x)
    idx = np.arange(1, n + 1)
    return float((2 * (idx * x_sorted).sum()) / (n * x.sum()) - (n + 1) / n)


def main():
    pkg = ["=== Chapter 3.4: team vs individual target build ==="]

    df = pd.read_csv(DATASET_IN, encoding="utf-8-sig", low_memory=False)
    pkg.append(f"model_dataset_women: shape={df.shape}")

    ae = pd.read_csv(AE_PATH, encoding="utf-8", low_memory=False)
    pkg.append(f"athlete_events: shape={ae.shape}")

    targets = build_targets(ae)
    pkg.append(f"targets built: shape={targets.shape}")

    df = df.merge(targets.drop(columns=["total_medals_from_ae"]), on=["NOC", "Year"], how="left")
    for c in ["team_medals", "individual_medals"]:
        df[c] = df[c].fillna(0).astype(int)

    df["team_share"] = np.where(
        df["team_medals"] + df["individual_medals"] > 0,
        df["team_medals"] / (df["team_medals"] + df["individual_medals"]),
        np.nan,
    )

    # Sanity: sum of team + individual should approximate mt_total
    total_check = df["team_medals"] + df["individual_medals"]
    diff = (df["mt_total"] - total_check).abs()
    pkg.append(f"\nSanity check: |mt_total - (team+individual)|")
    pkg.append(f"  mean diff = {diff.mean():.2f}   max = {diff.max():.0f}")
    pkg.append(f"  rows with diff > 5: {(diff > 5).sum()}  (expected: 2020/2024 attribution gap)")

    # Lag features
    df = df.sort_values(["NOC", "Year"]).reset_index(drop=True)
    df["lag_team_medals"] = df.groupby("NOC")["team_medals"].shift(1).fillna(0).astype(int)
    df["lag_individual_medals"] = df.groupby("NOC")["individual_medals"].shift(1).fillna(0).astype(int)

    df.to_csv(DATASET_OUT, index=False, encoding="utf-8-sig")
    pkg.append(f"\nmodel_dataset_team.csv saved: shape={df.shape}")

    # Concentration analysis (H3a)
    pkg.append("\n=== H3a: concentration of team vs individual medals ===")
    prim = df[df["sample_primary"] == 1]
    for col in ["team_medals", "individual_medals"]:
        vals = prim[col].values
        pkg.append(f"\n{col}:")
        pkg.append(f"  mean = {vals.mean():.2f}   max = {vals.max()}")
        pkg.append(f"  zero_share = {(vals == 0).mean():.3f}")
        pkg.append(f"  gini = {gini(vals):.3f}")
        top10 = np.sort(vals)[-10:].sum() / vals.sum() if vals.sum() > 0 else 0
        pkg.append(f"  top_10_share_of_all_medals = {top10:.3f}")

    # Per-edition descriptives
    pkg.append("\n=== per-edition means (primary sample) ===")
    for y in [1996, 2004, 2012, 2020, 2024]:
        sub = prim[prim["Year"] == y]
        if len(sub) == 0:
            continue
        pkg.append(
            f"  {y}: team={sub['team_medals'].mean():.2f}  "
            f"ind={sub['individual_medals'].mean():.2f}  "
            f"team_share_of_medals={sub['team_medals'].sum() / (sub['team_medals'].sum() + sub['individual_medals'].sum()):.3f}"
        )

    # Cross-tab: sports where team events dominate
    pkg.append("\n=== descriptive: sports by event-level team share ===")
    ae_sub = ae[(ae["Season"] == "Summer") & (ae["Medal"].notna())].copy()
    med = (
        ae_sub.groupby(["Sport", "Event", "Year", "NOC", "Medal"])["ID"].nunique()
        .reset_index(name="team_size")
    )
    med["is_team"] = (med["team_size"] > 1).astype(int)
    by_sport = med.groupby("Sport").agg(
        n_medals=("is_team", "size"),
        team_share=("is_team", "mean"),
    ).sort_values("team_share", ascending=False)
    pkg.append("\nTop 8 most team-oriented sports:")
    pkg.append(by_sport.head(8).round(3).to_string())
    pkg.append("\nTop 8 most individual-oriented sports:")
    pkg.append(by_sport.tail(8).round(3).to_string())

    report = ROOT / "reports" / "phase7b_team_targets.md"
    with open(report, "w", encoding="utf-8") as f:
        f.write("# Chapter 3.4 — Team vs Individual targets\n\n")
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
