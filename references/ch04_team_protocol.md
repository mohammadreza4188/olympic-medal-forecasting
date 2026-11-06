# Chapter 3.4 (Ch3 of dissertation) — Team vs Individual Medals

**Pre-registration date:** 2026-10-22
**Status:** Frozen.

## Research question
Do the same socioeconomic and gender features predict team-event medals and
individual-event medals with equal accuracy? Do feature importances differ?

## Targets (two separate count variables)
- `team_medals` — medals won in events where more than one athlete from the
  same NOC won in the same event and edition
- `individual_medals` — medals won in events where exactly one athlete from
  the NOC won

Both targets constructed from `athlete_events_through_2026.csv`, Summer only,
with the team-medal de-duplication rule from Chapter 1.

## Classification method (data-driven, primary)
For each (NOC, Year, Sport, Event, Medal) tuple:
- `team_size` = number of unique athlete IDs contributing to that medal
- team_size > 1 → team_medal
- team_size == 1 → individual_medal

This is objective and reproducible. A manual sport-level mapping is also
computed for descriptive reporting only, not for modeling.

## Leakage guards
- `team_events`, `ind_events`, `team_sports`, `ind_sports` (same-edition) are
  stored for descriptive tables but NOT used as features
- Only lagged versions enter the model
- `female_share` is used as a country-level covariate (pre-Games in reality)

## Feature blocks per target
Both targets use the same M1 macro block (10 features from protocol v1.1),
except the target-specific lag:
- Team model: `lag_team_medals` (replaces `lag_mt_total`)
- Individual model: `lag_individual_medals` (replaces `lag_mt_total`)
- Both keep `lag_mt_gold`

M1_noLag variants (drop lag) added for sensitivity.

## Hypotheses
- **H3a (concentration):** Team medals are more concentrated than individual
  medals (higher Gini, higher zero share, higher top-10 share)
- **H3b (predictability):** The same macro block predicts team medals with
  lower relative RMSE than individual medals, because team medals are
  concentrated in a small set of large countries
- **H3c (gender):** `female_share` has a larger marginal association with
  individual medals than with team medals

## Validation
Identical to protocols v1.1 and Ch2: forward-chaining on 2012, 2016, 2020,
2024; four families (Poisson, Hurdle, RF, XGB); seed 42; fixed
hyperparameters.

## Known limitations
- 2020 and 2024 `athlete_events` has 74 events per edition without medal
  attribution (Phase 0b). Team/individual split undercounts for those
  editions.
- "Team event" (e.g., 4x100m relay) is not identical to "team sport"
  (e.g., basketball). The former is used for classification; the latter
  appears only in descriptive tables.
- Two-target comparison uses identical features except the lag term, so
  improvements are attributable to target structure, not feature choice.
