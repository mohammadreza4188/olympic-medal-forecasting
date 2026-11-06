# Chapter 3.2 (Ch2 of dissertation) — Women's Participation

**Pre-registration date:** 2026-10-18 (before viewing evaluation results)
**Supersedes:** none
**Status:** Frozen.

## Research question
Do gender-disaggregated features improve out-of-sample prediction of a
country's total Summer Olympic medal count beyond `female_share`?

## Hypotheses
- **H2a (parsimony):** `female_share` in the macro block is sufficient;
  granular gender features do not improve prediction.
- **H2b (RCA-gender):** gender-disaggregated RCA features add predictive
  value beyond both `female_share` and the aggregate RCA block.
- **H2c (time trend):** the association between gender-specific features and
  medal count strengthens in post-2000 editions.

## Variants
- M1 (baseline): macro block including `female_share`
- M1_women: M1 + `log_female_athletes`, `lag_female_medal_share`,
  `female_athletes_to_pop_ratio`, `lag_female_medal_share_missing`
- M1_women_rca: M1_women + `rca_mean_weighted_female`,
  `n_sports_rca_gt1_female`, `medal_hhi_female`

## Leakage guards
- Same-edition female medal share is NOT a model input.
- Only participation-based or lagged features are used.

## Validation
Identical to phase 5 protocol v1.1: forward-chaining on 2012, 2016, 2020,
2024; four families (Poisson, Hurdle, RF, XGB); seed 42.

## Decision rule for H2a
M1_women beats M1 on RMSE by ≥3% mean across 4 editions, with positive
direction in ≥3/4 editions, in ≥3/4 families.

## Decision rule for H2b
M1_women_rca beats M1_women on RMSE by ≥3% mean, positive in ≥3/4 editions,
in ≥3/4 families.

## H2c status
Not formally tested in this chapter. Recorded as future work in Section 2.7.

## Known limitations
- `lag_female_medal_share` for 2024 inherits the 2020 athlete_events
  attribution gap.
- Many NOCs have no female-medal history; `_missing` flag handles structurally.
- In-edition female composition excluded as post-hoc.
