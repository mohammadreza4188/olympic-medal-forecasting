# Chapter 3.5 (Ch4 of dissertation) — Per-Sport Aggregation

**Pre-registration date:** 2026-10-22
**Status:** Frozen.

## Research question
Does modeling medals at the (NOC, Year, Sport) level and aggregating to
the country level produce more accurate predictions of a country's total
medal count than modeling the total directly?

## Why this is different from Chapter 3.4's bonus test
- Chapter 3.4 split medals into two groups (team, individual) and
  aggregated. No sub-target-specific features were used.
- Chapter 3.5 splits medals into ~25-30 sports, each with its own RCA
  feature block and sport-level controls. This is the actual test of
  whether sport-level specialization carries aggregable predictive signal.

## Hypotheses

- **H4a (aggregation beats direct):** The per-sport aggregate prediction
  beats the direct macro prediction (M1) and the naive baseline (M0) on
  RMSE, in at least 3 of 4 held-out editions.
- **H4b (sport-level signal):** The improvement of H4a, if any, is
  concentrated in countries with strong specialization (high `rca_max` in
  at least one sport).
- **H4c (correlation limit):** If H4a fails, the reason is positive
  correlation of per-sport prediction errors, not absence of signal.
  Diagnostic: measure pairwise error correlation.

## Sample

### Per-sport dataset
- Editions 1996–2024 (8 Summer editions).
- NOCs restricted to primary macro sample.
- Sports included if they appeared in at least 5 of the 8 editions.
- Expected: ~25 sports × 195 NOCs × 8 editions ≈ 40,000 rows before
  removal of country-sport non-participations.

### Aggregated evaluation
- Same primary sample as Chapters 1–3 (1,543 rows).
- Aggregation: sum of per-sport predictions for each (NOC, Year).

## Model

### Per-sport model (for each sport)
Predictors:
- Macro block from protocol v1.1 (10 features, including `lag_mt_total`)
- Sport-specific RCA for this country (rca, rca_log, sport_share_of_country_medals)
- Sport-level controls: `sport_total_events`, `sport_years_active`

Target: `medals_in_sport` for this (NOC, Year, Sport).

Families: XGBoost (`count:poisson`) and RandomForest.
Rationale: per-sport data is much sparser; simpler models likely overfit.

### Aggregation
- Sum the per-sport predictions.
- Do not scale or truncate.
- Compare to M0 (previous edition's total) and M1 (direct model from Ch1).

### Direct comparison model
Use the M1 result from Chapter 1 (already computed).

## Validation
- Forward-chaining, test years 2012, 2016, 2020, 2024.
- Training folds: all editions with official_year < Y.
- Per-sport models trained on same folds.

## Metrics
- RMSE, log_rmse, Spearman, Top-10 hit.
- Same as Chapters 1–3.

## Success criteria (pre-registered)
- **H4a confirmed** iff aggregation RMSE < M0 naive RMSE in ≥3 of 4
  editions, AND aggregation RMSE < M1 direct RMSE in ≥2 of 4 editions.
- **H4b confirmed** iff, in the subgroup with `rca_max > 1.5` in at
  least one sport, the aggregation gain is at least twice the gain in the
  rest of the sample.
- **H4c confirmed** iff H4a is rejected AND mean pairwise correlation
  of per-sport prediction errors exceeds 0.30.

## Known limitations
- 2020/2024 athlete_events attribution gap propagates to per-sport models
  for both editions. Per-sport training uses athlete_events, so training
  data for 2012 and 2016 includes the clean periods 1996–2008 and
  1996–2012 respectively, but test data for 2020/2024 is contaminated.
- Sports with unstable Olympic programs (introduced/removed mid-period)
  create a class of zero-heavy sub-targets where aggregation may add noise.
- Median filter: sports included in fewer than 5 of 8 editions are
  excluded.

## Deliverables
- `data/processed/per_sport_dataset.csv` — long format
- `src/models/train_eval_per_sport.py` — evaluation script
- `reports/phase7c_persport_results.md` — full results
- `reports/paper/ch04_persport.md` — written chapter
