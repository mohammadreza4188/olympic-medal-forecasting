# Research Protocol — Phase 5

**Version:** 1.0
**Date:** 2026-10-18
**Status:** Frozen. Any change is a new version.

## 1. Research question

Does the addition of discipline-level features — specifically Balassa revealed
comparative advantage (RCA) and its aggregates — improve out-of-sample prediction
of a country's total Summer Olympic medal count, beyond what is achievable with
macro-level socioeconomic and participation features?

Formally:
> Compare the predictive performance of a macro-only model M1 against
> a macro+discipline model M2 and a discipline-only model M3, under
> forward-chaining temporal validation, using identical outcomes, samples,
> and model classes.

## 2. Hypotheses

- **H1 (primary):** M2 outperforms M1 on RMSE by at least 3% relative improvement,
  averaged across the last four held-out editions.
- **H2:** M2 beats the naive benchmark M0 (previous edition's medal count) on RMSE,
  matching or exceeding the improvement reported by Schlembach et al. (2022).
- **H3 (exploratory):** M3 alone retains most of M2's improvement over M1, indicating
  that discipline features are the main source of incremental signal.
- **H4 (moderator):** The improvement of M2 over M1 is larger for countries
  with a revealed specialization profile (rca_max > 1.5 in at least one sport)
  than for countries without one.

- **Null H0:** Discipline features add no meaningful predictive value beyond
  macro features. If H1 is not supported by at least 3 of the 4 model families
  and 3 of the 4 held-out editions, we fail to reject H0.

## 3. Sample definition

### Primary sample
- Summer editions 1996–2024 (8 editions: 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024).
- Rationale: post-Cold War border stability, stable Olympic program, consistent WB coverage.
- Exclude NOCs in `NON_MAPPABLE_NOCS` (see World Bank protocol) — they have no macro features.
- Exclude MIX (mixed teams) — not a country.
- Exclude host years for the host country? **No.** Host is a feature, not a filter.

### Secondary sample
- Summer editions 1960–2024 (17 editions).
- Used for robustness only. Fewer editions means wider temporal validation but
  lower coverage on WB features pre-1990 and on discipline features pre-1960.

### Row count expectation
- Primary: ~8 editions × ~190 countries = ~1,520 country-edition rows.
- Secondary: ~17 editions × ~140 countries = ~2,380 rows.

## 4. Variables

### Dependent variable
- `mt_total` from medal_table_summary — count of total medals (gold+silver+bronze).
- Count outcome. Non-negative integer. Zero-inflated.

### Macro block (M1)
Primary specification:
- `log_gdp_const_avg4y` — log(1 + GDP constant 2015 US$, 4-year pre-Olympic average)
- `log_gdp_pcap_const_avg4y` — log(1 + GDP p.c., 4-year average)
- `log_population_avg4y` — log(1 + population, 4-year average)
- `host` — binary
- `athletes` — number of athletes sent (from athlete_events)
- `sports` — number of sports entered
- `events` — number of events entered
- `lag_total` — medal count in the previous edition (log1p)
- `lag_gold` — gold count in previous edition (log1p)
- `female_share` — female athletes / total athletes

`*_prev1y` versions of GDP and population are used in an alternative spec only.

### Discipline block (M2 = M1 + D)
Primary discipline block `D_base`: variant=total, window=last4, all 8 features:
- `rca_mean_weighted`, `rca_max`, `rca_p75`
- `n_sports_rca_gt1`, `n_sports_rca_gt1p5`
- `medal_hhi`, `n_sports_medal`, `medal_share_top_sport`

Alternative blocks (sensitivity only):
- `D_cum`: same 8 features, variant=total, window=cum
- `D_gender`: 6 features from female/last4 and male/last4 (rca_mean_weighted, n_sports_rca_gt1, medal_hhi)

### Transformations applied uniformly
- Log transform: `log1p` for GDP, population, all medal counts, all RCA aggregates
  except counts (`n_sports_*` which are already small integers).
- Winsorize at the 99th percentile: all `rca_*` features, `medal_hhi`,
  `medal_share_top_sport`. Reason: RCA blow-up for single-medal countries
  (see Phase 4b report — AFG rca=95.97).
- NaN discipline features (country had zero medals in window) → **fill with 0**.
  This is conceptually valid: zero medals in window means zero revealed specialization.
  Add flag `has_discipline_data = int(not all_nan_before_fill)`.
- NaN macro features: **do not impute**. Drop at model time. Document row loss.

## 5. Model specifications

Four model families, applied identically to M0/M1/M2/M3:

### M0 — Naive
- Prediction = medal count in previous edition for that country.
- If country did not appear in previous edition: prediction = 0.
- No training required.

### M1 — Macro only
### M2 — Macro + D_base (primary hypothesis test)
### M3 — Discipline only

Within M1/M2/M3, four model classes:

1. **Negative Binomial GLM** (statsmodels) — interpretable count model.
2. **Hurdle model** — logistic (any medal?) × NB (count | any medal).
   Mirrors Schlembach's two-stage logic.
3. **Random Forest** (sklearn, `RandomForestRegressor`) — nonparametric benchmark.
4. **XGBoost** (`XGBRegressor` with `objective='count:poisson'`) — strongest nonparametric
   count-specific alternative.

All hyperparameters tuned by inner 3-fold CV within each training window.

## 6. Validation

### Forward-chaining (rolling origin)
For target edition Y_t, train on all editions with official_year < Y_t, test on Y_t.
Roll forward through the last four editions of the sample:

- Primary sample (1996–2024): test on 2012, 2016, 2020, 2024. Train on 1996–(Y_t-1).
- Secondary sample (1960–2024): test on 2008, 2012, 2016, 2020, 2024.

Never use random splits. Ever. Not even for hyperparameter tuning across time.

### Hyperparameter search
Within each training window, 3-fold time-series CV (scikit-learn `TimeSeriesSplit`)
selects the configuration that minimizes Poisson deviance on validation folds.

## 7. Metrics

Reported per test edition and averaged across the 4 held-out editions:

- **RMSE** — primary decision metric.
- **MAE** — robustness.
- **Poisson deviance** — for count-specific calibration.
- **Spearman rank correlation** on country-level medal totals — ranking quality.
- **Top-10 hit rate** — fraction of true top-10 medal countries recovered in the
  model's top-10 predictions.
- **Naive gap** — percentage relative improvement over M0 on RMSE.

## 8. Success criteria (pre-registered)

- **H1 supported** iff:
  - M2 vs M1 relative RMSE improvement ≥ 3% averaged across 4 held-out editions, AND
  - Direction of improvement is positive in ≥ 3 of 4 held-out editions, AND
  - Pattern holds in ≥ 3 of 4 model families (NB, Hurdle, RF, XGB).

- **H2 supported** iff M2 beats M0 in ≥ 3 of 4 held-out editions, for at least one
  model family.

- **H3 supported** iff M3's average RMSE is within 10% of M2's average RMSE —
  indicating that most of the improvement over M1 comes from discipline features.

- **H4 supported** iff the M2-vs-M1 RMSE gap is at least twice as large in the
  high-specialization subgroup as in the low-specialization subgroup.

- **H0 not rejected** if any of H1's three sub-conditions fails.

## 9. Sensitivity analyses (secondary)

Each is run and reported in a single table without being used as a primary claim:

1. Replace `avg4y` with `prev1y` for GDP and population.
2. Replace `D_base` with `D_cum`.
3. Add `D_gender` block.
4. Sample 1960–2024 (secondary sample).
5. Winsorize RCA at 95th percentile instead of 99th.
6. Drop `lag_total` (test whether discipline block subsumes lagged medals).

## 10. Reporting rules

- Correlation, prediction, and causal inference are distinguished in every
  sentence. Language like "RCA drives medals" is banned. Language like
  "RCA is associated with higher medal counts" is used.
- All figures show the naive benchmark M0 alongside M1/M2/M3.
- All tables report both RMSE and the naive gap.
- No claim of novelty in the abstract or introduction until the literature
  table in `references/literature_table.csv` is finalized.
- Code + data (except WB raw) + trained model cards are placed in `src/` and
  `reports/` and versioned with git commits at each gate.

## 11. Known limitations (documented upfront)

- 2020/2024 athlete_events have 74 events per edition missing medal attribution
  (Phase 0b audit). This affects `lag_*` and `D_base` features for target 2024.
  Magnitude unknown; will be flagged as a caveat in the results section.
- The 1996 cutoff excludes editions with major geopolitical disruptions but also
  removes interesting variation. Robustness on the 1960–2024 sample is reported.
- The primary success threshold (3%) is pre-registered and is intentionally modest.
  A larger, statistically significant improvement is not required by this protocol,
  but any absence of improvement at this threshold is reported honestly.

## 12. Deliverables at end of Phase 6

- `data/processed/model_dataset.csv` — merged, transformed, model-ready.
- `src/models/train_eval.py` — one script that runs all model × variant combinations,
  writes results tables and figures.
- `reports/phase6_results.md` — full results, including all sensitivity analyses.
- `reports/phase6_model_cards.md` — one short card per model family describing
  inputs, hyperparameters chosen per window, and residual diagnostics.
- `figures/` — RMSE by edition and model (bar plot), Spearman by edition (line plot),
  M2-vs-M1 delta heatmap by model family.
