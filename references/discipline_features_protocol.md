# Discipline-Level Features & Balassa RCA — Phase 4b

## Purpose
Construct country-by-sport specialization features from `athlete_events_through_2026.csv`
and aggregate them to country-edition rows so they can be merged into `panel_summer_macro_v2.csv`.

## Source of truth
All discipline features come from the athlete-level dataset, **not** from the medal table.
Reason: `medal_table_summary.csv` has no sport breakdown.

## Medal definition (team rule)
A medal is defined as one (NOC, Edition, Sport, Event, Medal-type) tuple.
`drop_duplicates(subset=[NOC, Year, Season, Sport, Event, Medal])` before aggregation.
This gives one medal per country per event per medal type, matching Olympic convention.

## RCA (Balassa) definition
For country c, sport s, reference window W:

    RCA[c,s,W] = ( m[c,s,W] / m[c,·,W] ) / ( m[·,s,W] / m[·,·,W] )

where m denotes the medal count in the window.
Interpretation: RCA > 1 means the country wins a larger share of that sport's medals
than its overall share of all medals. Standard revealed comparative advantage.

Edge cases:
- If m[c,·,W] = 0 (country has no medals in window), all RCA[c,·,W] = NaN.
- If m[·,·,W] = 0 (no medals recorded in window), all RCA = NaN.
- If m[c,s,W] = 0 but m[c,·,W] > 0, RCA[c,s,W] = 0 (not specialized).
- If m[·,s,W] = 0, sport is not in window; row omitted.

## Reference windows
Two windows per target edition Y:
- `cum` — all editions with official_year < Y. Cumulative history.
- `last4` — the four most recent editions with official_year < Y. Recency-weighted.

Reason for two: cumulative RCA captures long-term specialization identity;
last-4y RCA captures current specialization profile. Both are diagnostic and both
are candidates for the final model.

## Variants
For each window, compute four versions:
- `total` — all medals
- `gold` — gold medals only
- `female` — medals won by female athletes only (Sex == F)
- `male` — medals won by male athletes only (Sex == M)

Mixed events: an athlete is attributed to their own Sex. If a mixed event is won
by a team with both sexes, the medal is credited to both the female and male
variants. This is a documented simplification.

## Features per (NOC, Year, window, variant)
- `rca_mean_weighted` — medal-weighted average RCA across sports with medals
- `rca_max` — maximum RCA across sports
- `rca_p75` — 75th percentile of RCA across sports
- `n_sports_rca_gt1` — count of sports with RCA > 1 (revealed specialization)
- `n_sports_rca_gt1p5` — count with RCA > 1.5 (strong specialization)
- `medal_hhi` — Herfindahl index of medal shares across sports (0 = uniform, 1 = single sport)
- `n_sports_medal` — number of distinct sports with at least one medal
- `medal_share_top_sport` — share of medals from the most-medaled sport

## Known limitation
`athlete_events_through_2026.csv` for 2020 and 2024 is missing medal attribution
for 74 events per edition (see phase0b audit). Consequently:
- RCA features for target Year = 2024 include 2020 in both windows. Bias magnitude
  unknown. Flagged as a caveat in the merge report.
- RCA features for target Year ≤ 2020 are unaffected.

## Output
- `data/processed/discipline_features.csv` — long format, one row per
  (NOC, Year, window, variant) with the eight feature columns above.
- `data/processed/discipline_sport_medals.csv` — long format, one row per
  (NOC, Year, window, variant, Sport) with medals and RCA (for diagnostics and
  for any future per-sport modeling).
- `reports/phase4b_discipline_features.md` — coverage summary, sample rows,
  and top-specialized-sport diagnostics for a few countries.
